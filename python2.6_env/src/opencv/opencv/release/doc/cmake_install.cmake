# Install script for directory: /myPython/src/opencv/opencv/doc

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
  FILE(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/opencv/doc" TYPE FILE FILES
    "/myPython/src/opencv/opencv/doc/ChangeLog.htm"
    "/myPython/src/opencv/opencv/doc/haartraining.htm"
    "/myPython/src/opencv/opencv/doc/index.htm"
    "/myPython/src/opencv/opencv/doc/CMakeLists.txt"
    "/myPython/src/opencv/opencv/doc/license.txt"
    "/myPython/src/opencv/opencv/doc/packaging.txt"
    "/myPython/src/opencv/opencv/doc/README.txt"
    "/myPython/src/opencv/opencv/doc/opencv.jpg"
    "/myPython/src/opencv/opencv/doc/opencv-logo.png"
    "/myPython/src/opencv/opencv/doc/opencv-logo2.png"
    "/myPython/src/opencv/opencv/doc/opencv.pdf"
    "/myPython/src/opencv/opencv/doc/opencv_cheatsheet.pdf"
    "/myPython/src/opencv/opencv/doc/pattern.pdf"
    )
ENDIF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "main")

IF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "main")
  FILE(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/opencv/doc/papers" TYPE FILE FILES
    "/myPython/src/opencv/opencv/doc/papers/algo_tracking.pdf"
    "/myPython/src/opencv/opencv/doc/papers/camshift.pdf"
    "/myPython/src/opencv/opencv/doc/papers/avbpa99.ps"
    )
ENDIF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "main")

IF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "main")
  FILE(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/opencv/doc/vidsurv" TYPE FILE FILES
    "/myPython/src/opencv/opencv/doc/vidsurv/Blob_Tracking_Modules.doc"
    "/myPython/src/opencv/opencv/doc/vidsurv/Blob_Tracking_Tests.doc"
    "/myPython/src/opencv/opencv/doc/vidsurv/TestSeq.doc"
    )
ENDIF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "main")

