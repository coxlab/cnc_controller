# Install script for directory: /myPython/src/opencv/opencv/modules/objdetect

# Set the install prefix
IF(NOT DEFINED CMAKE_INSTALL_PREFIX)
  SET(CMAKE_INSTALL_PREFIX "/myPython")
ENDIF(NOT DEFINED CMAKE_INSTALL_PREFIX)
STRING(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
IF(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  IF(BUILD_TYPE)
    STRING(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  ELSE(BUILD_TYPE)
    SET(CMAKE_INSTALL_CONFIG_NAME "Release")
  ENDIF(BUILD_TYPE)
  MESSAGE(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
ENDIF(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)

# Set the component getting installed.
IF(NOT CMAKE_INSTALL_COMPONENT)
  IF(COMPONENT)
    MESSAGE(STATUS "Install component: \"${COMPONENT}\"")
    SET(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  ELSE(COMPONENT)
    SET(CMAKE_INSTALL_COMPONENT)
  ENDIF(COMPONENT)
ENDIF(NOT CMAKE_INSTALL_COMPONENT)

IF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "main")
  IF("${CMAKE_INSTALL_CONFIG_NAME}" MATCHES "^([Dd][Ee][Bb][Uu][Gg])$")
    FILE(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE SHARED_LIBRARY FILES
      "/myPython/src/opencv/opencv/release/lib/libopencv_objdetect.2.1.1.dylib"
      "/myPython/src/opencv/opencv/release/lib/libopencv_objdetect.2.1.dylib"
      "/myPython/src/opencv/opencv/release/lib/libopencv_objdetect.dylib"
      )
    FOREACH(file
        "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libopencv_objdetect.2.1.1.dylib"
        "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libopencv_objdetect.2.1.dylib"
        "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libopencv_objdetect.dylib"
        )
      IF(EXISTS "${file}" AND
         NOT IS_SYMLINK "${file}")
        EXECUTE_PROCESS(COMMAND "/usr/bin/install_name_tool"
          -id "/myPython/lib/libopencv_objdetect.2.1.dylib"
          -change "/myPython/src/opencv/opencv/release/lib/libopencv_core.2.1.dylib" "/myPython/lib/libopencv_core.2.1.dylib"
          -change "/myPython/src/opencv/opencv/release/lib/libopencv_imgproc.2.1.dylib" "/myPython/lib/libopencv_imgproc.2.1.dylib"
          "${file}")
        IF(CMAKE_INSTALL_DO_STRIP)
          EXECUTE_PROCESS(COMMAND "/usr/bin/strip" "${file}")
        ENDIF(CMAKE_INSTALL_DO_STRIP)
      ENDIF()
    ENDFOREACH()
  ENDIF("${CMAKE_INSTALL_CONFIG_NAME}" MATCHES "^([Dd][Ee][Bb][Uu][Gg])$")
  IF("${CMAKE_INSTALL_CONFIG_NAME}" MATCHES "^([Rr][Ee][Ll][Ee][Aa][Ss][Ee])$")
    FILE(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE SHARED_LIBRARY FILES
      "/myPython/src/opencv/opencv/release/lib/libopencv_objdetect.2.1.1.dylib"
      "/myPython/src/opencv/opencv/release/lib/libopencv_objdetect.2.1.dylib"
      "/myPython/src/opencv/opencv/release/lib/libopencv_objdetect.dylib"
      )
    FOREACH(file
        "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libopencv_objdetect.2.1.1.dylib"
        "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libopencv_objdetect.2.1.dylib"
        "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libopencv_objdetect.dylib"
        )
      IF(EXISTS "${file}" AND
         NOT IS_SYMLINK "${file}")
        EXECUTE_PROCESS(COMMAND "/usr/bin/install_name_tool"
          -id "/myPython/lib/libopencv_objdetect.2.1.dylib"
          -change "/myPython/src/opencv/opencv/release/lib/libopencv_core.2.1.dylib" "/myPython/lib/libopencv_core.2.1.dylib"
          -change "/myPython/src/opencv/opencv/release/lib/libopencv_imgproc.2.1.dylib" "/myPython/lib/libopencv_imgproc.2.1.dylib"
          "${file}")
        IF(CMAKE_INSTALL_DO_STRIP)
          EXECUTE_PROCESS(COMMAND "/usr/bin/strip" "${file}")
        ENDIF(CMAKE_INSTALL_DO_STRIP)
      ENDIF()
    ENDFOREACH()
  ENDIF("${CMAKE_INSTALL_CONFIG_NAME}" MATCHES "^([Rr][Ee][Ll][Ee][Aa][Ss][Ee])$")
ENDIF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "main")

IF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "main")
  FILE(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/opencv2/objdetect" TYPE FILE FILES "/myPython/src/opencv/opencv/modules/objdetect/include/opencv2/objdetect/objdetect.hpp")
ENDIF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "main")

