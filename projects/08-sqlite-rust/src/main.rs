use std::env;
use std::fs::File;
use std::io::{Read, Seek, SeekFrom};

fn read_header(path: &str) -> std::io::Result<()> {
    let mut file = File::open(path)?;
    let mut header = [0u8; 100];
    file.read_exact(&mut header)?;

    let sig = std::str::from_utf8(&header[0..16]).unwrap_or("<invalid>");
    let page_size = u16::from_be_bytes([header[16], header[17]]);
    let write_ver = header[18];
    let read_ver = header[19];
    let page_count = u32::from_be_bytes([header[28], header[29], header[30], header[31]]);

    println!("signature: {}", sig.trim_end_matches('\0'));
    println!("page_size: {}", if page_size == 1 { 65536 } else { page_size as u32 });
    println!("write_version: {}", write_ver);
    println!("read_version: {}", read_ver);
    println!("page_count: {}", page_count);

    Ok(())
}

fn read_page(path: &str, page_no: u32) -> std::io::Result<()> {
    let mut file = File::open(path)?;
    let mut header = [0u8; 100];
    file.read_exact(&mut header)?;
    let raw_size = u16::from_be_bytes([header[16], header[17]]);
    let page_size = if raw_size == 1 { 65536usize } else { raw_size as usize };

    if page_no == 0 {
        eprintln!("page number starts at 1");
        std::process::exit(1);
    }

    let offset = ((page_no as u64) - 1) * (page_size as u64);
    file.seek(SeekFrom::Start(offset))?;
    let mut page = vec![0u8; page_size];
    file.read_exact(&mut page)?;

    let page_start = if page_no == 1 { 100 } else { 0 };
    let page_type = page[page_start];
    let first_freeblock = u16::from_be_bytes([page[page_start + 1], page[page_start + 2]]);
    let cell_count = u16::from_be_bytes([page[page_start + 3], page[page_start + 4]]);
    let cell_content_area = u16::from_be_bytes([page[page_start + 5], page[page_start + 6]]);

    let kind = match page_type {
        0x02 => "Interior Index B-Tree",
        0x05 => "Interior Table B-Tree",
        0x0A => "Leaf Index B-Tree",
        0x0D => "Leaf Table B-Tree",
        _ => "Unknown",
    };

    println!("page: {}", page_no);
    println!("page_type: 0x{:02X} ({})", page_type, kind);
    println!("first_freeblock: {}", first_freeblock);
    println!("cell_count: {}", cell_count);
    println!("cell_content_area: {}", cell_content_area);

    Ok(())
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 3 {
        eprintln!("usage: sqlite-rust <header|page> <file> [page_no]");
        std::process::exit(1);
    }

    match args[1].as_str() {
        "header" => {
            if let Err(err) = read_header(&args[2]) {
                eprintln!("error: {}", err);
                std::process::exit(1);
            }
        }
        "page" => {
            if args.len() != 4 {
                eprintln!("usage: sqlite-rust page <file> <page_no>");
                std::process::exit(1);
            }
            let page_no: u32 = args[3].parse().unwrap_or(0);
            if let Err(err) = read_page(&args[2], page_no) {
                eprintln!("error: {}", err);
                std::process::exit(1);
            }
        }
        _ => {
            eprintln!("unknown command");
            std::process::exit(1);
        }
    }
}
