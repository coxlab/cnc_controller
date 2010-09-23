//
//  main.m
//  pyCocoa
//
//  Created by Brett Graham on 12/5/09.
//  Copyright 2009 Harvard University. All rights reserved.
//

#import <Cocoa/Cocoa.h>


int main(int argc, char *argv[])
{
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    
    NSBundle *mainBundle = [NSBundle mainBundle];
    NSString *resourcePath = [mainBundle resourcePath];
    NSString *virtualEnvPath = @"/myPython/";
    
    NSArray *pythonPathArray = [NSArray arrayWithObjects: resourcePath,
                                @"/System/Library/Frameworks/Python.framework/Versions/2.6/Extras/lib/python/PyObjC/",
                                nil];
    
    setenv("PYTHONPATH", [[pythonPathArray componentsJoinedByString:@":"] UTF8String], 1);
    
    setenv("VIRTUAL_ENV", [virtualEnvPath UTF8String], 1);
    
    NSArray *possibleMainExtensions = [NSArray arrayWithObjects: @"py", @"pyc", @"pyo", nil];
    NSString *mainFilePath = nil;
    
    for (NSString *possibleMainExtension in possibleMainExtensions) {
        mainFilePath = [mainBundle pathForResource: @"main" ofType: possibleMainExtension];
        if ( mainFilePath != nil ) break;
    }
    
	if ( !mainFilePath ) {
        [NSException raise: NSInternalInconsistencyException format: @"%s:%d main() Failed to find the Main.{py,pyc,pyo} file in the application wrapper's Resources directory.", __FILE__, __LINE__];
    }
    
    Py_SetProgramName([[virtualEnvPath stringByAppendingPathComponent:@"bin/python"] cString]);
    
    Py_SetPythonHome([virtualEnvPath cString]);
    
    Py_Initialize();
    PySys_SetArgv(argc, (char **)argv);
    
    const char *mainFilePathPtr = [mainFilePath UTF8String];
    FILE *mainFile = fopen(mainFilePathPtr, "r");
    int result = PyRun_SimpleFile(mainFile, (char *)[[mainFilePath lastPathComponent] UTF8String]);
    
    if ( result != 0 )
        [NSException raise: NSInternalInconsistencyException
                    format: @"%s:%d main() PyRun_SimpleFile failed with file '%@'.  See console for errors.", __FILE__, __LINE__, mainFilePath];
    
    [pool drain];
    
    return result;
    
//    // TODO: check for the existence of Python 2.6
//#define USE_PYTHON_26
//    
//#ifdef USE_PYTHON_26
//    NSArray *pythonPathArray = [NSArray arrayWithObjects: resourcePath,
//                                [resourcePath stringByAppendingPathComponent:@"PyObjC"],
//                                [resourcePath stringByAppendingPathComponent:@"SupportingModules"],
//                                @"/System/Library/Frameworks/Python.framework/Versions/2.6/Extras/lib/python/PyObjC/", nil];
//#else
//    NSArray *pythonPathArray = [NSArray arrayWithObjects: resourcePath,
//                                [resourcePath stringByAppendingPathComponent:@"PyObjC"],
//                                [resourcePath stringByAppendingPathComponent:@"SupportingModules"],
//                                @"/System/Library/Frameworks/Python.framework/Versions/2.5/Extras/lib/python/PyObjC/", nil];
//#endif
//    //NSArray *pythonPathArray = [NSArray arrayWithObjects: resourcePath, [resourcePath stringByAppendingPathComponent:@"PyObjC"], @"/System/Library/Frameworks/Python.framework/Versions/Current/Extras/lib/python/", "/Library/Python/", nil];
//    //NSArray *pythonPathArray = [NSArray arrayWithObjects: resourcePath, [resourcePath stringByAppendingPathComponent:@"PyObjC"], @"/System/Library/Frameworks/Python.framework/Versions/2.5/Extras/lib/python/PyObjC/", @"/Library/Python/2.5/site-packages/",  @"/Library/Python/", nil];
//    //NSArray *pythonPathArray = [NSArray arrayWithObjects: resourcePath, @"/System/Library/Frameworks/Python.framework/Versions/2.5/Extras/lib/python/PyObjC/", @"/System/Library/Frameworks/Python.framework/Versions/2.5/Extras/lib/python/", @"/Library/Python/2.5/site-packages", nil];
//    
//    //setenv("PYTHONHOME", "/System/Library/Frameworks/Python.framework/Versions/2.5/", 1);
//    setenv("PYTHONPATH", [[pythonPathArray componentsJoinedByString:@":"] UTF8String], 1);
//    
//    // This is to make the POS ctypes binding work
//    setenv("VIRTUAL_ENV", [[resourcePath stringByAppendingPathComponent:@"python2.6_env"] UTF8String], 1);
//    
//    NSArray *possibleMainExtensions = [NSArray arrayWithObjects: @"py", @"pyc", @"pyo", nil];
//    NSString *mainFilePath = nil;
//    
//    for (NSString *possibleMainExtension in possibleMainExtensions) {
//        mainFilePath = [mainBundle pathForResource: @"main" ofType: possibleMainExtension];
//        if ( mainFilePath != nil ) break;
//    }
//    
//	if ( !mainFilePath ) {
//        [NSException raise: NSInternalInconsistencyException format: @"%s:%d main() Failed to find the Main.{py,pyc,pyo} file in the application wrapper's Resources directory.", __FILE__, __LINE__];
//    }
//    
//    
//#ifdef USE_PYTHON_26
//    Py_SetProgramName([[resourcePath stringByAppendingPathComponent:@"python2.6_env/bin/python"] cString]);
//#else
//    Py_SetProgramName("/usr/bin/python2.5");
//#endif
//    
//    
//#ifdef USE_PYTHON_26
//    Py_SetPythonHome([[resourcePath stringByAppendingPathComponent:@"python2.6_env"] cString]);
//#else
//    Py_SetPythonHome([[resourcePath stringByAppendingPathComponent:@"python_env"] cString]);
//#endif
//    
//    Py_Initialize();
//    PySys_SetArgv(argc, (char **)argv);
//    
//    const char *mainFilePathPtr = [mainFilePath UTF8String];
//    FILE *mainFile = fopen(mainFilePathPtr, "r");
//    int result = PyRun_SimpleFile(mainFile, (char *)[[mainFilePath lastPathComponent] UTF8String]);
//    
//    if ( result != 0 )
//        [NSException raise: NSInternalInconsistencyException
//                    format: @"%s:%d main() PyRun_SimpleFile failed with file '%@'.  See console for errors.", __FILE__, __LINE__, mainFilePath];
//    
//    [pool drain];
//    
//    return result;
}
