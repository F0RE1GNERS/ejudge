use std::io;
fn main() {
    // variable declaration
    let mut num_str_1 = String::new();
    let mut num_str_2 = String::new();

    // read variables
    io::stdin().read_line(&mut num_str_1).ok().expect("read error");
    io::stdin().read_line(&mut num_str_2).ok().expect("read error");

    // parse integers
    let mut num_1 : i32 = num_str_1.trim().parse().ok().expect("parse error");
    let mut num_2 : i32 = num_str_2.trim().parse().ok().expect("parse error");

    // print the sum
    // Hint: Type println!("{}", num_1 + num_2);) below
    println!("{}", num_1 + num_2);
}