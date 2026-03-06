use regex::Regex;
use std::env;
use std::fs::File;
use std::io::{self, BufRead, BufReader};

fn run<R: BufRead>(reader: R, re: &Regex) {
    for line in reader.lines() {
        if let Ok(text) = line {
            if re.is_match(&text) {
                println!("{}", text);
            }
        }
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 || args.len() > 3 {
        eprintln!("usage: grep-rust <pattern> [file]");
        std::process::exit(1);
    }

    let pattern = &args[1];
    let re = match Regex::new(pattern) {
        Ok(v) => v,
        Err(err) => {
            eprintln!("invalid pattern: {}", err);
            std::process::exit(1);
        }
    };

    if args.len() == 3 {
        let file = match File::open(&args[2]) {
            Ok(f) => f,
            Err(err) => {
                eprintln!("failed to open file: {}", err);
                std::process::exit(1);
            }
        };
        run(BufReader::new(file), &re);
    } else {
        let stdin = io::stdin();
        run(stdin.lock(), &re);
    }
}
