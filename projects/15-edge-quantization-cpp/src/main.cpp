#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
#include <tuple>
#include <vector>

struct Args {
    int samples = 8000;
    int features = 256;
    int classes = 8;
    int iters = 200;
    int seed = 42;
};

struct DataSet {
    std::vector<float> x;
    std::vector<int> y;
    int n = 0;
    int d = 0;
    int c = 0;
};

struct QuantizedTensor {
    std::vector<int8_t> q;
    std::vector<float> scale_per_row;
    int rows = 0;
    int cols = 0;
};

static Args parse_args(int argc, char** argv) {
    Args args;
    for (int i = 1; i < argc; ++i) {
        std::string k = argv[i];
        auto next_int = [&](int& ref) {
            if (i + 1 < argc) {
                ref = std::stoi(argv[++i]);
            }
        };
        if (k == "--samples") next_int(args.samples);
        else if (k == "--features") next_int(args.features);
        else if (k == "--classes") next_int(args.classes);
        else if (k == "--iters") next_int(args.iters);
        else if (k == "--seed") next_int(args.seed);
    }
    return args;
}

static DataSet make_synth_rna_dataset(const Args& args) {
    std::mt19937 rng(args.seed);
    std::normal_distribution<float> noise(0.0f, 0.15f);

    DataSet ds;
    ds.n = args.samples;
    ds.d = args.features;
    ds.c = args.classes;
    ds.x.resize(static_cast<size_t>(ds.n) * ds.d);
    ds.y.resize(ds.n);

    int block = std::max(1, ds.d / ds.c);
    for (int i = 0; i < ds.n; ++i) {
        int label = i % ds.c;
        ds.y[i] = label;
        for (int j = 0; j < ds.d; ++j) {
            float v = noise(rng);
            int start = label * block;
            int end = std::min(ds.d, start + block);
            if (j >= start && j < end) v += 1.0f;
            ds.x[static_cast<size_t>(i) * ds.d + j] = v;
        }
    }
    return ds;
}

static std::vector<float> init_weights(int classes, int features, int seed) {
    std::mt19937 rng(seed + 7);
    std::normal_distribution<float> dist(0.0f, 0.1f);
    std::vector<float> w(static_cast<size_t>(classes) * features);
    for (auto& v : w) v = dist(rng);
    return w;
}

static std::vector<float> model_logits_fp32(const std::vector<float>& x, const std::vector<float>& w, int n, int d, int c) {
    std::vector<float> out(static_cast<size_t>(n) * c, 0.0f);
    for (int i = 0; i < n; ++i) {
        for (int cls = 0; cls < c; ++cls) {
            float s = 0.0f;
            const float* x_ptr = &x[static_cast<size_t>(i) * d];
            const float* w_ptr = &w[static_cast<size_t>(cls) * d];
            for (int j = 0; j < d; ++j) s += x_ptr[j] * w_ptr[j];
            out[static_cast<size_t>(i) * c + cls] = s;
        }
    }
    return out;
}

static int argmax_row(const float* row, int c) {
    int best = 0;
    float best_v = row[0];
    for (int i = 1; i < c; ++i) {
        if (row[i] > best_v) {
            best_v = row[i];
            best = i;
        }
    }
    return best;
}

static float accuracy_from_logits(const std::vector<float>& logits, const std::vector<int>& y, int n, int c) {
    int ok = 0;
    for (int i = 0; i < n; ++i) {
        int p = argmax_row(&logits[static_cast<size_t>(i) * c], c);
        ok += (p == y[i]);
    }
    return static_cast<float>(ok) / std::max(1, n);
}

static std::vector<float> collect_activation_abs(const std::vector<float>& x) {
    std::vector<float> a(x.size());
    for (size_t i = 0; i < x.size(); ++i) a[i] = std::fabs(x[i]);
    return a;
}

static float kl_divergence(const std::vector<float>& p, const std::vector<float>& q) {
    const float eps = 1e-12f;
    float s = 0.0f;
    for (size_t i = 0; i < p.size(); ++i) {
        if (p[i] > 0.0f) s += p[i] * std::log((p[i] + eps) / (q[i] + eps));
    }
    return s;
}

static float calibrate_kl_threshold(const std::vector<float>& abs_acts, int bins = 2048, int qbins = 128) {
    float max_v = *std::max_element(abs_acts.begin(), abs_acts.end());
    if (max_v <= 0.0f) return 1.0f;

    std::vector<float> hist(bins, 0.0f);
    for (float v : abs_acts) {
        int b = std::min(bins - 1, static_cast<int>(v / max_v * (bins - 1)));
        hist[b] += 1.0f;
    }
    float hist_sum = std::accumulate(hist.begin(), hist.end(), 0.0f);
    for (auto& h : hist) h /= std::max(hist_sum, 1.0f);

    float best_t = max_v;
    float best_kl = 1e30f;
    for (int t = qbins; t < bins; ++t) {
        std::vector<float> p(t, 0.0f);
        for (int i = 0; i < t; ++i) p[i] = hist[i];
        float tail = 0.0f;
        for (int i = t; i < bins; ++i) tail += hist[i];
        p[t - 1] += tail;

        std::vector<float> q(t, 0.0f);
        int group = std::max(1, t / qbins);
        for (int i = 0; i < qbins; ++i) {
            int l = i * group;
            int r = std::min(t, (i + 1) * group);
            if (l >= t) break;
            float mass = 0.0f;
            for (int j = l; j < r; ++j) mass += p[j];
            float avg = mass / std::max(1, r - l);
            for (int j = l; j < r; ++j) q[j] = avg;
        }
        float kl = kl_divergence(p, q);
        if (kl < best_kl) {
            best_kl = kl;
            best_t = max_v * (static_cast<float>(t) / bins);
        }
    }
    return std::max(best_t, 1e-6f);
}

static QuantizedTensor quantize_ptq_int8(const std::vector<float>& w, int rows, int cols) {
    float max_abs = 0.0f;
    for (float v : w) max_abs = std::max(max_abs, std::fabs(v));
    float scale = std::max(max_abs / 127.0f, 1e-8f);

    QuantizedTensor qt;
    qt.rows = rows;
    qt.cols = cols;
    qt.scale_per_row.assign(rows, scale);
    qt.q.resize(w.size());
    for (size_t i = 0; i < w.size(); ++i) {
        int qv = static_cast<int>(std::round(w[i] / scale));
        qv = std::max(-127, std::min(127, qv));
        qt.q[i] = static_cast<int8_t>(qv);
    }
    return qt;
}

static QuantizedTensor quantize_awq_int8(const std::vector<float>& w, int rows, int cols, const std::vector<float>& act_mean_abs) {
    QuantizedTensor qt;
    qt.rows = rows;
    qt.cols = cols;
    qt.q.resize(w.size());
    qt.scale_per_row.resize(rows, 1.0f);

    for (int r = 0; r < rows; ++r) {
        float weighted_max = 0.0f;
        for (int c = 0; c < cols; ++c) {
            float v = std::fabs(w[static_cast<size_t>(r) * cols + c]) * (act_mean_abs[c] + 1e-3f);
            weighted_max = std::max(weighted_max, v);
        }
        float scale = std::max(weighted_max / 127.0f, 1e-8f);
        qt.scale_per_row[r] = scale;
        for (int c = 0; c < cols; ++c) {
            float ww = w[static_cast<size_t>(r) * cols + c] * (act_mean_abs[c] + 1e-3f);
            int qv = static_cast<int>(std::round(ww / scale));
            qv = std::max(-127, std::min(127, qv));
            qt.q[static_cast<size_t>(r) * cols + c] = static_cast<int8_t>(qv);
        }
    }
    return qt;
}

static std::vector<float> logits_quantized(const std::vector<float>& x, const QuantizedTensor& qw, int n, int d, int c, float act_clip) {
    std::vector<float> out(static_cast<size_t>(n) * c, 0.0f);
    float x_scale = std::max(act_clip / 127.0f, 1e-8f);

    std::vector<int8_t> xq(static_cast<size_t>(n) * d);
    for (size_t i = 0; i < x.size(); ++i) {
        float clipped = std::max(-act_clip, std::min(act_clip, x[i]));
        int v = static_cast<int>(std::round(clipped / x_scale));
        v = std::max(-127, std::min(127, v));
        xq[i] = static_cast<int8_t>(v);
    }

    for (int i = 0; i < n; ++i) {
        for (int cls = 0; cls < c; ++cls) {
            int32_t acc = 0;
            const int8_t* x_ptr = &xq[static_cast<size_t>(i) * d];
            const int8_t* w_ptr = &qw.q[static_cast<size_t>(cls) * d];
            for (int j = 0; j < d; ++j) acc += static_cast<int32_t>(x_ptr[j]) * static_cast<int32_t>(w_ptr[j]);
            out[static_cast<size_t>(i) * c + cls] = static_cast<float>(acc) * x_scale * qw.scale_per_row[cls];
        }
    }
    return out;
}

static std::vector<float> feature_mean_abs(const std::vector<float>& x, int n, int d) {
    std::vector<float> m(d, 0.0f);
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < d; ++j) m[j] += std::fabs(x[static_cast<size_t>(i) * d + j]);
    }
    for (float& v : m) v /= std::max(1, n);
    return m;
}

template <typename Fn>
static double time_ms(Fn&& fn, int iters) {
    auto t0 = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iters; ++i) fn();
    auto t1 = std::chrono::high_resolution_clock::now();
    double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    return ms / std::max(1, iters);
}

int main(int argc, char** argv) {
    Args args = parse_args(argc, argv);
    auto ds = make_synth_rna_dataset(args);
    auto w = init_weights(args.classes, args.features, args.seed);

    auto acts = collect_activation_abs(ds.x);
    float act_clip = calibrate_kl_threshold(acts);
    auto act_mean = feature_mean_abs(ds.x, ds.n, ds.d);

    auto qw_ptq = quantize_ptq_int8(w, ds.c, ds.d);
    auto qw_awq = quantize_awq_int8(w, ds.c, ds.d, act_mean);

    auto fp_logits = model_logits_fp32(ds.x, w, ds.n, ds.d, ds.c);
    float fp_acc = accuracy_from_logits(fp_logits, ds.y, ds.n, ds.c);

    auto ptq_logits = logits_quantized(ds.x, qw_ptq, ds.n, ds.d, ds.c, act_clip);
    float ptq_acc = accuracy_from_logits(ptq_logits, ds.y, ds.n, ds.c);

    auto awq_logits = logits_quantized(ds.x, qw_awq, ds.n, ds.d, ds.c, act_clip);
    float awq_acc = accuracy_from_logits(awq_logits, ds.y, ds.n, ds.c);

    double fp_ms = time_ms([&]() {
        volatile auto out = model_logits_fp32(ds.x, w, ds.n, ds.d, ds.c);
        (void)out;
    }, args.iters);

    double ptq_ms = time_ms([&]() {
        volatile auto out = logits_quantized(ds.x, qw_ptq, ds.n, ds.d, ds.c, act_clip);
        (void)out;
    }, args.iters);

    double awq_ms = time_ms([&]() {
        volatile auto out = logits_quantized(ds.x, qw_awq, ds.n, ds.d, ds.c, act_clip);
        (void)out;
    }, args.iters);

    std::cout << std::fixed << std::setprecision(4);
    std::cout << "scheme,accuracy,latency_ms,speedup_vs_fp32\n";
    std::cout << "fp32," << fp_acc << "," << fp_ms << ",1.0000\n";
    std::cout << "ptq_int8," << ptq_acc << "," << ptq_ms << "," << (fp_ms / ptq_ms) << "\n";
    std::cout << "awq_int8," << awq_acc << "," << awq_ms << "," << (fp_ms / awq_ms) << "\n";

    std::ofstream report("QUANT_REPORT.md");
    report << "# Project B Quantization Report\n\n";
    report << "Config: samples=" << args.samples << ", features=" << args.features
           << ", classes=" << args.classes << ", iters=" << args.iters << "\n\n";
    report << "KL calibrated activation clip: " << act_clip << "\n\n";
    report << "| Scheme | Accuracy | Latency (ms) | Speedup vs FP32 |\n";
    report << "|---|---:|---:|---:|\n";
    report << "| FP32 | " << fp_acc << " | " << fp_ms << " | 1.0000 |\n";
    report << "| PTQ int8 | " << ptq_acc << " | " << ptq_ms << " | " << (fp_ms / ptq_ms) << " |\n";
    report << "| AWQ int8 | " << awq_acc << " | " << awq_ms << " | " << (fp_ms / awq_ms) << " |\n\n";
    report << "Pareto note: choose points with best latency for acceptable accuracy degradation.\n";
    report.close();

    std::cout << "report written: QUANT_REPORT.md\n";
    return 0;
}
