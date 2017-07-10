import java.io.*;
import java.util.*;
import java.text.*;
import java.math.*;
import java.util.regex.*;

public class Main {

    public static void main(String[] args) {
        try {
            FileReader in = new FileReader("/tmp/unsafe.txt");
            BufferedReader buffer = new BufferedReader(in);
            String token = buffer.readLine();
            buffer.close();
            in.close();
            System.out.println(token);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
