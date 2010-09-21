# Install script for directory: /myPython/src/opencv/opencv/modules

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

IF(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for each subdirectory.
  INCLUDE("/myPython/src/opencv/opencv/release/modules/calib3d/cmake_install.cmake")
  INCLUDE("/myPython/src/opencv/opencv/release/modules/core/cmake_install.cmake")
  INCLUDE("/myPython/src/opencv/opencv/release/modules/features2d/cmake_install.cmake")
  INCLUDE("/myPython/src/opencv/opencv/release/modules/highgui/cmake_install.cmake")
  INCLUDE("/myPython/src/opencv/opencv/release/modules/imgproc/cmake_install.cmake")
  INCLUDE("/myPython/src/opencv/opencv/release/modules/legacy/cmake_install.cmake")
  INCLUDE("/myPython/src/opencv/opencv/release/modules/contrib/cmake_install.cmake")
  INCLUDE("/myPython/src/opencv/opencv/release/modules/ml/cmake_install.cmake")
  INCLUDE("/myPython/src/opencv/opencv/release/modules/objdetect/cmake_install.cmake")
  INCLUDE("/myPython/src/opencv/opencv/release/modules/python/cmake_install.cmake")
  INCLUDE("/myPython/src/opencv/opencv/release/modules/video/cmake_install.cmake")
  INCLUDE("/myPython/src/opencv/opencv/release/modules/haartraining/cmake_install.cmake")
  INCLUDE("/myPython/src/opencv/opencv/release/modules/traincascade/cmake_install.cmake")
  INCLUDE("/myPython/src/opencv/opencv/release/modules/gpu/cmake_install.cmake")

ENDIF(NOT CMAKE_INSTALL_LOCAL_ONLY)

