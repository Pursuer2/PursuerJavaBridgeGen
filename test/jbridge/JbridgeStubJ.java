package jbridge;

public class JbridgeStubJ {
	public static String printAndReturn(int a) {
		System.out.print("java side:");
		System.out.println(Integer.toString(a,16));
		return Integer.toString(a,16);
	}
	public static native byte[] printByteArray(byte[] buf);
}
