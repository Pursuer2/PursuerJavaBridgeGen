

from . import _commonfile

import typing

primitiveType=['boolean','byte','short','int','long','float','double','void']

import io
import os

class JavaClassStub:
    def __init__(self):
        self.cNamespace:str='undef'
        self.__prepared=False

    def loadBySource(self,source:str):
        from javalang import parse
        self._parsed=parse.parse(source)
    
    def loadByPath(self,path:str):
        with io.open(path,'rb') as fd:
            self.loadByIO(fd)
    
    def loadByIO(self,readable:io.BufferedIOBase):
        txt=readable.read().decode('utf-8')
        self.loadBySource(txt)
    
    def __cvtJNameToCName(self,jname:str)->str:
        return '/'.join(jname.split('.'))
    
    
    def doPrepare(self):
        if not self.__prepared:
            self.__prepared=True
            self.packageName=self._parsed.package.name
            publicMethod=[x for x in self._parsed.types[0].methods \
                           if 'public' in x.modifiers and 'static' in x.modifiers]
            self.toExport=[x for x in publicMethod if not 'native' in x.modifiers]
            self.toImport=[x for x in publicMethod if 'native' in x.modifiers]
            self.bclsName=self.__cvtJNameToCName(self.packageName+'.'+self._parsed.types[0].name)
            self.classMap={}
            for imp in self._parsed.imports:
                if not imp.wildcard:
                    self.classMap[imp.path[imp.path.rindex('.')+1:]]=imp.path
            if self.cNamespace=='undef':
                self.cNamespace='jbridge_'+self._parsed.types[0].name+'_'
    
        
    
    def __typeInfer(self,typeName:str)->str:
        if typeName in ('Object','String'):
            return 'java.lang.'+typeName
        elif typeName in self.classMap:
            return self.classMap[typeName]
        elif '.' in typeName or typeName in primitiveType: 
            return typeName
        else:
            return self.packageName+'.'+typeName
    
        
    def __getSignByType(self,typeName:str,arrayDim:int)->str:
        typeName=self.__typeInfer(typeName)
        sign=''
        if typeName=='boolean':
            sign= 'Z'
        elif typeName=='byte':
            sign= 'B'
        elif typeName=='short':
            sign= 'S'
        elif typeName=='int':
            sign= 'I'
        elif typeName=='long':
            sign= 'J'
        elif typeName=='float':
            sign= 'F'
        elif typeName=='double':
            sign= 'D'
        elif typeName=='void':
            sign= 'V'
        else:
            sign= 'L'+self.__cvtJNameToCName(typeName)+';'
        
        return '['*arrayDim+sign
    
    def __getMethodSign(self,method)->str:
        msign='('
        for para in method.parameters:
            msign+=self.__getSignByType(para.type.name,len(para.type.dimensions))
        msign+=')'+self.__getSignByType(method.return_type.name if method.return_type!=None else 'void',len(para.type.dimensions))
        return msign
    
    def __JtypeToCtype(self,jtype)->str:
        ctype=''
        if jtype==None:
            ctype='void'
        elif len(jtype.dimensions)==0:
            if jtype.name=='int':
                ctype='int32_t'
            elif jtype.name=='long':
                ctype.name='int64_t'
            elif jtype.name=='float':
                ctype='float'
            elif jtype.name=='double':
                ctype='double'
            elif jtype.name=='boolean' or jtype=='char':
                ctype='int8_t'
            elif jtype.name=='short':
                ctype='int16_t'
            else:
                ctype='void *'
        else:
            ctype='void *'
        return ctype
    
    def __GetCArgList(self,jmethod,firstArg:str):
        return '(%s)'%', '.join([firstArg]+[self.__JtypeToCtype(x.type)+' '+x.name for x in jmethod.parameters])
    
    def writeDefAndVar(self,stream):
        stream.write('static const char* %s_methodName[]={\n'%self.cNamespace)
        stream.write(','.join(['"'+method.name+'"' for method in self.toExport]))
        stream.write('};\n')

        stream.write('static const char* %s_methodSig[]={\n'%self.cNamespace)
        stream.write(','.join(['"'+self.__getMethodSign(method)+'"' for method in self.toExport]))
        stream.write('};\n')

        stream.write('#define _%s_METHOD_COUNT %d\n'%(self.cNamespace,len(self.toExport)))
        stream.write('''
static jobject %s_clazz=NULL;
static jmethodID %s_jmethodIDList[_%s_METHOD_COUNT];
static struct %s_Interface %s_InterfaceImpl;
'''%tuple([self.cNamespace]*5))
    
    def writeMethodStub(self,stream):
        for index,method in enumerate(self.toExport):
            returnType=self.__JtypeToCtype(method.return_type)
            stream.write('static %s %s_method%d%s{\n'%(returnType,self.cNamespace,\
                                                       index,self.__GetCArgList(method,'void *jenv2')))
            stream.write('\tJNIEnv *jenv=jenv2;\n')
            stream.write('\t')
            paramsList=','.join(['jenv','%s_clazz'%self.cNamespace,'%s_jmethodIDList[%d]'%(self.cNamespace,index)]+[x.name for x in method.parameters])
            if method.return_type==None:
                stream.write('(*jenv)->CallStaticVoidMethod(%s);\n'%paramsList)
            elif method.return_type.name in primitiveType and len(method.return_type.dimensions)==0:
                stream.write('return (*jenv)->CallStatic%sMethod(%s);\n'%(method.return_type.name.capitalize(),paramsList))
            else:
                stream.write('return (*jenv)->CallStaticObjectMethod(%s);\n'%paramsList)
            stream.write('}\n')
    
    def writeNativeMethodStub(self,stream):
        stream.write('#define _%s_NATIVE_METHOD_COUNT %d\n'%(self.cNamespace,len(self.toImport)))
        for index,method in enumerate(self.toImport):
            paramList=self.__GetCArgList(method,'JNIEnv *jenv,jclass _j0')
            argList=','.join(['jenv']+[x.name for x in method.parameters])
            retType=self.__JtypeToCtype(method.return_type)
            stream.write('''JNICALL static %s %s_nmethod%d%s{
    if(%s_InterfaceImpl.%s!=NULL){\n\t\t'''%tuple([retType,self.cNamespace,index,paramList]+[self.cNamespace,method.name]))
            stream.write('' if retType=='void' else 'return ')
            stream.write('''%s_InterfaceImpl.%s(%s);
    }
}\n'''%tuple([self.cNamespace,method.name]+[argList]))
            
        stream.write('static JNINativeMethod %s_nativeMethods[]={\n'%self.cNamespace)
        nMetLs=[]
        for index,method in enumerate(self.toImport):
            nMetLs.append('{"%s","%s",%s_nmethod%d}'%(method.name,self.__getMethodSign(method),self.cNamespace,index))
        stream.write('\n,\t'.join(nMetLs))
        stream.write('\n};\n')
                
    def writeExportQueryInterfaceFunc(self,stream):
        stream.write('''int %s_QueryInterface(void *jenv,struct %s_Interface **pInterface){
    *pInterface=&%s_InterfaceImpl;
    return 0;
}\n\n'''%tuple([self.cNamespace]*3))
    
    def writeInitCode(self,stream)->str:
        stream.write('''static void %s_mod_init(JNIEnv *jenv){
    jclass clsobj=(*jenv)->FindClass(jenv,"%s");
    %s_clazz=(*jenv)->NewGlobalRef(jenv,clsobj);
    (*jenv)->DeleteLocalRef(jenv,clsobj);
    for(int i=0;i<_%s_METHOD_COUNT;i++){
        %s_jmethodIDList[i]=(*jenv)->GetStaticMethodID(jenv,%s_clazz,
        %s_methodName[i],%s_methodSig[i]);
    }\n'''%tuple([self.cNamespace]+[self.bclsName]+[self.cNamespace]*6))
        stream.write('\tstruct %s_Interface *impl=&%s_InterfaceImpl;\n'%(self.cNamespace,self.cNamespace))
        for index,method in enumerate(self.toExport):
            stream.write('\timpl->%s=%s_method%d;\n'%(method.name,self.cNamespace,index))
        stream.write('\t(*jenv)->RegisterNatives(jenv,%s_clazz,%s_nativeMethods,_%s_NATIVE_METHOD_COUNT);\n'%tuple([self.cNamespace]*3))
        stream.write('}\n')
        return '%s_mod_init'%self.cNamespace
    


    def writeDeclare(self,stream):
        stream.write('struct %s_Interface{\n'%self.cNamespace)
        for method in self.toExport+self.toImport:
            stream.write('\t%s (*%s)%s;\n'%(self.__JtypeToCtype(method.return_type),method.name,self.__GetCArgList(method,'void *jenv')))
        stream.write('};\n')
        
        stream.write('int %s_QueryInterface(void *jenv,struct %s_Interface **pInterface);\n'%(self.cNamespace,self.cNamespace))
        
        
        
def generate(stubs:typing.List[JavaClassStub],decltio,stubtio):
    decltio.write(_commonfile.declFile)
    for s in stubs:
        s.doPrepare()
        s.writeDeclare(decltio)
    decltio.write('\n#endif')
    
    stubtio.write(_commonfile.jnienvStub)
    initFunc=[]
    for s in stubs:
        s.writeDefAndVar(stubtio)
        s.writeMethodStub(stubtio)
        s.writeNativeMethodStub(stubtio)
        initFunc.append(s.writeInitCode(stubtio)+'(jenv);')
        s.writeExportQueryInterfaceFunc(stubtio)
    stubtio.write(_commonfile.generateJniLoadHandler(initFunc,[]))
    
    
def generateToDir(stubs:typing.List[JavaClassStub],dirPath:str):
    with io.open(os.path.sep.join([dirPath,'jbridge_decl.h']),'w') as declFile ,\
    io.open(os.path.sep.join([dirPath,'jbridge_stub.c']),'w') as stubFile:
        generate(stubs,declFile,stubFile)