# PursuerJavaBridgeGen 

This is a code generator to generate C jni glue code according to the java files.(also support android.)

## How to test and use

1.  install dependency by 
`python -m pip install -r requirements.txt`

2. run test by
`python test.py`
(jni.h,jni_md.h is not included in this project, So if jni.h is not found, please specify the C_INCLUDE_PATH to your jdk include path)

3.  see "test.py" , "test/jbridge_test.c" , "test/jbridge/JbridgeStubJ.java"  for usage.

you need write a Java class with "public static" methods to be exported, like file "test/jbridge/JbridgeStubJ.java". and access these methods by include generated "jbridge_decl.h" in c code. See test/jbridge_test.c.

For "native" method, your programe should overwrite the function in struct jbridge_xxxx__Interface. 

## Remark
the class signature is infered by the import list, So use fullname import if class in other package used by method declaration(except java.lang.String)

you can generate multi-class by pass all java files into PursuerJavaBridgeGen.generateToDir

the generated jbridge_decl.h can be used without jni.h