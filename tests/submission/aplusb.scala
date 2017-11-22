import scala.io.StdIn._

object Main extends App {
    println(io.Source.stdin.getLines().map(_.toInt).sum)
}
