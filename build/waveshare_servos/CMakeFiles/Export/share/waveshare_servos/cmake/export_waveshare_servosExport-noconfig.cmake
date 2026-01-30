#----------------------------------------------------------------
# Generated CMake target import file.
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "waveshare_servos::waveshare_servos" for configuration ""
set_property(TARGET waveshare_servos::waveshare_servos APPEND PROPERTY IMPORTED_CONFIGURATIONS NOCONFIG)
set_target_properties(waveshare_servos::waveshare_servos PROPERTIES
  IMPORTED_LOCATION_NOCONFIG "${_IMPORT_PREFIX}/lib/libwaveshare_servos.so"
  IMPORTED_SONAME_NOCONFIG "libwaveshare_servos.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS waveshare_servos::waveshare_servos )
list(APPEND _IMPORT_CHECK_FILES_FOR_waveshare_servos::waveshare_servos "${_IMPORT_PREFIX}/lib/libwaveshare_servos.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
