# ===================================================================================
#  The OpenCV CMake configuration file
#
#             ** File generated automatically, do not modify **
#
#  Usage from an external project:
#    In your CMakeLists.txt, add these lines:
#
#    FIND_PACKAGE(OpenCV REQUIRED )
#    TARGET_LINK_LIBRARIES(MY_TARGET_NAME ${OpenCV_LIBS})
#
#    This file will define the following variables:
#      - OpenCV_LIBS                 : The list of libraries to links against.
#      - OpenCV_LIB_DIR              : The directory where lib files are. Calling LINK_DIRECTORIES
#                                      with this path is NOT needed.
#      - OpenCV_INCLUDE_DIRS         : The OpenCV include directories.
#      - OpenCV_COMPUTE_CAPABILITIES : The version of compute capability
#      - OpenCV_VERSION              : The version of this OpenCV build. Example: "1.2.0"
#      - OpenCV_VERSION_MAJOR        : Major version part of OpenCV_VERSION. Example: "1"
#      - OpenCV_VERSION_MINOR        : Minor version part of OpenCV_VERSION. Example: "2"
#      - OpenCV_VERSION_PATCH        : Patch version part of OpenCV_VERSION. Example: "0"
#
# =================================================================================================

# ======================================================
# Version Compute Capability from which library OpenCV
# has been compiled is remembered
# ======================================================
SET(OpenCV_COMPUTE_CAPABILITIES )

# Extract the directory where *this* file has been installed (determined at cmake run-time)
#  This variable may or may not be used below, depending on the parsing of OpenCVConfig.cmake
get_filename_component(THIS_OPENCV_CONFIG_PATH "${CMAKE_CURRENT_LIST_FILE}" PATH)

# ======================================================
# Include directories to add to the user project:
# ======================================================
INCLUDE_DIRECTORIES(/myPython/include/opencv;/myPython/include)
# Provide the include directories to the caller
SET(OpenCV_INCLUDE_DIRS /myPython/include/opencv;/myPython/include)

# ======================================================
# Link directories to add to the user project:
# ======================================================
LINK_DIRECTORIES("/myPython/lib")
# Provide the libs directory anyway, it may be needed in some cases.
SET(OpenCV_LIB_DIR "/myPython/lib")

# ====================================================================
# Link libraries: e.g.   opencv_core220.so, opencv_imgproc220d.lib, etc...
# ====================================================================
set(OPENCV_LIB_COMPONENTS opencv_core opencv_imgproc opencv_features2d opencv_gpu opencv_calib3d opencv_objdetect opencv_video opencv_highgui opencv_ml opencv_legacy opencv_contrib)
SET(OpenCV_LIBS "")
foreach(__CVLIB ${OPENCV_LIB_COMPONENTS})
	# CMake>=2.6 supports the notation "debug XXd optimized XX"
	if (CMAKE_MAJOR_VERSION GREATER 2  OR  CMAKE_MINOR_VERSION GREATER 4)
		# Modern CMake:
		SET(OpenCV_LIBS ${OpenCV_LIBS} debug ${__CVLIB} optimized ${__CVLIB})
	else(CMAKE_MAJOR_VERSION GREATER 2  OR  CMAKE_MINOR_VERSION GREATER 4)
		# Old CMake:
		SET(OpenCV_LIBS ${OpenCV_LIBS} ${__CVLIB})
	endif(CMAKE_MAJOR_VERSION GREATER 2  OR  CMAKE_MINOR_VERSION GREATER 4)
endforeach(__CVLIB)

# ==============================================================
#  Extra include directories, needed by OpenCV 2 new structure
# ==============================================================
if(NOT "" STREQUAL  "")
	SET(BASEDIR "")
	foreach(__CVLIB ${OPENCV_LIB_COMPONENTS})
		# We only need the "core",... part here: "opencv_core" -> "core"
		STRING(REGEX REPLACE "opencv_(.*)" "\\1" MODNAME ${__CVLIB})
		INCLUDE_DIRECTORIES("${BASEDIR}/modules/${MODNAME}/include")
	endforeach(__CVLIB)
endif(NOT "" STREQUAL  "")

# For OpenCV built as static libs, we need the user to link against
#  many more dependencies:
IF (NOT 1)
	# Under static libs, the user of OpenCV needs access to the 3rdparty libs as well:
	LINK_DIRECTORIES("/myPython/src/opencv/opencv/release/3rdparty/lib")

	SET(OpenCV_LIBS
		
		
		
		
		
		
		
		${OpenCV_LIBS}) # The standard libs BEFORE (OpenCV_LIBS) since these can have "debug","optimized".
ENDIF(NOT 1)


# ======================================================
#  Version variables:
# ======================================================
SET(OpenCV_VERSION 2.1.1)
SET(OpenCV_VERSION_MAJOR  2)
SET(OpenCV_VERSION_MINOR  1)
SET(OpenCV_VERSION_PATCH  1)
