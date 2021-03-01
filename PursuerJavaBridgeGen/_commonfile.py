
import typing

declFile='''
#ifndef _JBRIDGE_DECL_H
#define _JBRIDGE_DECL_H

#include <stdint.h>
#include <stddef.h>

struct jbridge_bytearray_access{
    void *_internalObj;
    size_t size;
    char *buf;
};

struct jbridge_string_access{
    void *_internalObj;
    size_t size;
    const char *utf;
};

struct jbridge_jnienv_Interface{
    int (*TryAttachThread)(void **jenv);
    void (*DetachThread)(void *jenv);
    void (*NewJByteArray)(void *jenv,void **jbytearray,size_t len);
    void (*AccessJByteArray)(void *jenv,void *jbytearray,struct jbridge_bytearray_access *out);
    void (*ReleaseJByteArray)(void *jenv,struct jbridge_bytearray_access *toRelease);
    void (*NewJString)(void *jenv,void **jstring,char *utf);
    void (*AccessJString)(void *jenv,void *jstring,struct jbridge_string_access *out);
    void (*ReleaseJString)(void *jenv,struct jbridge_string_access *toRelease);
};

int jbridge_jnienv_QueryInterface(struct jbridge_jnienv_Interface **interface);


'''


jnienvStub='''

#include "jbridge_decl.h"

#include "jni.h"
#include <stdlib.h>
#ifndef jbridge_malloc
#define jbridge_malloc malloc
#endif
#ifndef jbridge_free
#define jbridge_free free
#endif


JavaVM *g_jvm=NULL;

static int jbridge_jnienv_TryAttachThread(void **jenv){
    jint result=(*g_jvm)->GetEnv(g_jvm,jenv,JNI_VERSION_1_6);
    if(result!=JNI_OK){
        // convert to void * to avoid warning message due to different jni.h
        result=(*g_jvm)->AttachCurrentThread(g_jvm,(void *)jenv,NULL);
    }
    if(result!=JNI_OK){
        return -1;
    }else{
        return 0;
    }
}

static void jbridge_jnienv_DetachThread(void *jenv){
    (*g_jvm)->DetachCurrentThread(g_jvm);
}

static void jbridge_jnienv_NewJByteArray(void *jenv2,void **jbytearray,size_t len){
    JNIEnv *jenv=jenv2;
    *jbytearray=(*jenv)->NewByteArray(jenv,len);
}
static void jbridge_jnienv_AccessJByteArray(void *jenv2,void *jbytearray,struct jbridge_bytearray_access *out){
    JNIEnv *jenv=jenv2;
    jboolean isCopy=JNI_FALSE;
    out->_internalObj=jbytearray;
    out->size=(*jenv)->GetArrayLength(jenv,jbytearray);
    out->buf=(char *)(*jenv)->GetByteArrayElements(jenv,jbytearray,&isCopy);
}
static void jbridge_jnienv_ReleaseJByteArray(void *jenv2,struct jbridge_bytearray_access *toRelease){
    JNIEnv *jenv=jenv2;
    (*jenv)->ReleaseByteArrayElements(jenv,toRelease->_internalObj,(jbyte *)toRelease->buf,0);
}

static void jbridge_jnienv_NewJString(void *jenv2,void **jstr,char *utf){
    JNIEnv *jenv=jenv2;
    *jstr=(*jenv)->NewStringUTF(jenv,utf);
}
static void jbridge_jnienv_AccessJString(void *jenv2,void *jstr,struct jbridge_string_access *out){
    JNIEnv *jenv=jenv2;
    jboolean isCopy=JNI_FALSE;
    out->size=(*jenv)->GetStringUTFLength(jenv,jstr);
    out->utf=(*jenv)->GetStringUTFChars(jenv,jstr,&isCopy);
}
static void jbridge_jnienv_ReleaseJString(void *jenv2,struct jbridge_string_access *toRelease){
    JNIEnv *jenv=jenv2;
    (*jenv)->ReleaseStringUTFChars(jenv,toRelease->_internalObj,toRelease->utf);
}

struct jbridge_jnienv_Interface *jbridge_jnienv_InterfaceImpl=NULL;
int jbridge_jnienv_QueryInterface(struct jbridge_jnienv_Interface **pInterface){
    if(jbridge_jnienv_InterfaceImpl==NULL){
        jbridge_jnienv_InterfaceImpl=jbridge_malloc(sizeof(struct jbridge_jnienv_Interface));
        struct jbridge_jnienv_Interface *impl=jbridge_jnienv_InterfaceImpl;
        impl->TryAttachThread=&jbridge_jnienv_TryAttachThread;
        impl->DetachThread=&jbridge_jnienv_DetachThread;
        impl->NewJByteArray=&jbridge_jnienv_NewJByteArray;
        impl->AccessJByteArray=&jbridge_jnienv_AccessJByteArray;
        impl->ReleaseJByteArray=&jbridge_jnienv_ReleaseJByteArray;
        impl->NewJString=&jbridge_jnienv_NewJString;
        impl->AccessJString=&jbridge_jnienv_AccessJString;
        impl->ReleaseJString=&jbridge_jnienv_ReleaseJString;
    }
    *pInterface=jbridge_jnienv_InterfaceImpl;
    return 0;
}


'''

jniLoadHandler='''

jint JNI_OnLoad(JavaVM *vm, void* reserved){
    g_jvm=vm;
    JNIEnv *jenv;
    (*vm)->GetEnv(vm,(void **)&jenv,JNI_VERSION_1_6);
    %s
    return JNI_VERSION_1_6;
}

void JNI_OnUnload(JavaVM *vm, void *reserved){
    %s
}

'''

def generateJniLoadHandler(initFunc:typing.List[str],deinitFunc:typing.List[str]):
    return jniLoadHandler%('\n\t'.join(initFunc),'\n\t'.join(deinitFunc))
    