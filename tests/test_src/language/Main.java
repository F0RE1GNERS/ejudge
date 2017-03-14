import java.util.Date;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.RuntimeException;

public class Main {
    public static void main(String[] args) {
        try {
            FileWriter writer = new FileWriter("/tmp/100001.txt");
            writer.write("aaa");
            writer.close();
        } catch (IOException e) {
            e.printStackTrace();
            throw new RuntimeException();
        }
    }
}
