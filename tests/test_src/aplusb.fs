// The entire code is given, you can just review and submit!
open System

[<EntryPoint>]
let main argv =
    let a = Console.ReadLine() |> int
    let b = Console.ReadLine() |> int
    printfn "%d" (a+b)
    0 // return an integer exit code
