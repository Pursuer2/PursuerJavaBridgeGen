
#include "jbridge_decl.h"

#include "stdio.h"
#include "jni.h"

void *native_printByteArray(void *jenv, void *buf){
    struct jbridge_jnienv_Interface *jb;
    jbridge_jnienv_QueryInterface(&jb);
    struct jbridge_bytearray_access ja;
    jb->AccessJByteArray(jenv,buf,&ja);
    printf("c side:len %d,content %x,%x,%x,%x\n",ja.size,ja.buf[0],ja.buf[1],ja.buf[2],ja.buf[3]);
    ja.buf[3]++;
    jb->ReleaseJByteArray(jenv,&ja);
    return buf;
}

//JNI Entry
JNIEXPORT JNICALL
void Java_jbridge_Example_testEntry(void *jni1,void *jni2){
    
    struct jbridge_jnienv_Interface *jb;
    jbridge_jnienv_QueryInterface(&jb);
    void *jenv;
    jb->TryAttachThread(&jenv);
    struct jbridge_JbridgeStubJ__Interface *jbs;
    jbridge_JbridgeStubJ__QueryInterface(jenv,&jbs);
    void *jstr=jbs->printAndReturn(jenv,0x1234);
    struct jbridge_string_access js;
    jb->AccessJString(jenv,jstr,&js);
    printf("c side:%s\n",js.utf);
    jb->ReleaseJString(jenv,&js);
    jbs->printByteArray=native_printByteArray;
    
}
