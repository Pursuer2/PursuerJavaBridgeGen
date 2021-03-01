package jbridge;

import java.io.File;
import java.io.UnsupportedEncodingException;

public class Example {
	public static void main(String[] args) {
		System.out.println("start test...");
		File f=new File("./jbridge_stub.dll");
		System.load(f.getAbsolutePath());
		System.out.println("dll load done...");
		testEntry();
		try {
			byte[] jb=JbridgeStubJ.printByteArray(new byte[]{1,2,3,4});
            System.out.println("java side(+1):"+jb[0]+","+jb[1]+","+jb[2]+","+jb[3]);
		} catch (Exception e) {
		}
        System.out.println("test done...");
	}
	public static native void testEntry();
	
}
