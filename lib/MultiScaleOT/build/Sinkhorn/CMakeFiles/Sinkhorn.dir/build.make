# CMAKE generated file: DO NOT EDIT!
# Generated by "Unix Makefiles" Generator, CMake Version 3.12

# Delete rule output on recipe failure.
.DELETE_ON_ERROR:


#=============================================================================
# Special targets provided by cmake.

# Disable implicit rules so canonical targets will work.
.SUFFIXES:


# Remove some rules from gmake that .SUFFIXES does not remove.
SUFFIXES =

.SUFFIXES: .hpux_make_needs_suffix_list


# Suppress display of executed commands.
$(VERBOSE).SILENT:


# A target that is always out of date.
cmake_force:

.PHONY : cmake_force

#=============================================================================
# Set environment variables for the build.

# The shell in which to execute make rules.
SHELL = /bin/sh

# The CMake executable.
CMAKE_COMMAND = /usr/local/lib/python2.7/dist-packages/cmake/data/bin/cmake

# The command to remove a file.
RM = /usr/local/lib/python2.7/dist-packages/cmake/data/bin/cmake -E remove -f

# Escaping for special characters.
EQUALS = =

# The top-level source directory on which CMake was run.
CMAKE_SOURCE_DIR = "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/src"

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build"

# Include any dependencies generated for this target.
include Sinkhorn/CMakeFiles/Sinkhorn.dir/depend.make

# Include the progress variables for this target.
include Sinkhorn/CMakeFiles/Sinkhorn.dir/progress.make

# Include the compile flags for this target's objects.
include Sinkhorn/CMakeFiles/Sinkhorn.dir/flags.make

Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornSolver.cpp.o: Sinkhorn/CMakeFiles/Sinkhorn.dir/flags.make
Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornSolver.cpp.o: /content/gdrive/MyDrive/Colab\ Notebooks/DomDecKeOps/lib/MultiScaleOT/src/Sinkhorn/TSinkhornSolver.cpp
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir="/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/CMakeFiles" --progress-num=$(CMAKE_PROGRESS_1) "Building CXX object Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornSolver.cpp.o"
	cd "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/Sinkhorn" && /usr/bin/c++  $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -o CMakeFiles/Sinkhorn.dir/TSinkhornSolver.cpp.o -c "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/src/Sinkhorn/TSinkhornSolver.cpp"

Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornSolver.cpp.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing CXX source to CMakeFiles/Sinkhorn.dir/TSinkhornSolver.cpp.i"
	cd "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/Sinkhorn" && /usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -E "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/src/Sinkhorn/TSinkhornSolver.cpp" > CMakeFiles/Sinkhorn.dir/TSinkhornSolver.cpp.i

Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornSolver.cpp.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling CXX source to assembly CMakeFiles/Sinkhorn.dir/TSinkhornSolver.cpp.s"
	cd "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/Sinkhorn" && /usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -S "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/src/Sinkhorn/TSinkhornSolver.cpp" -o CMakeFiles/Sinkhorn.dir/TSinkhornSolver.cpp.s

Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornKernel.cpp.o: Sinkhorn/CMakeFiles/Sinkhorn.dir/flags.make
Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornKernel.cpp.o: /content/gdrive/MyDrive/Colab\ Notebooks/DomDecKeOps/lib/MultiScaleOT/src/Sinkhorn/TSinkhornKernel.cpp
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir="/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/CMakeFiles" --progress-num=$(CMAKE_PROGRESS_2) "Building CXX object Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornKernel.cpp.o"
	cd "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/Sinkhorn" && /usr/bin/c++  $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -o CMakeFiles/Sinkhorn.dir/TSinkhornKernel.cpp.o -c "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/src/Sinkhorn/TSinkhornKernel.cpp"

Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornKernel.cpp.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing CXX source to CMakeFiles/Sinkhorn.dir/TSinkhornKernel.cpp.i"
	cd "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/Sinkhorn" && /usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -E "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/src/Sinkhorn/TSinkhornKernel.cpp" > CMakeFiles/Sinkhorn.dir/TSinkhornKernel.cpp.i

Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornKernel.cpp.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling CXX source to assembly CMakeFiles/Sinkhorn.dir/TSinkhornKernel.cpp.s"
	cd "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/Sinkhorn" && /usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -S "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/src/Sinkhorn/TSinkhornKernel.cpp" -o CMakeFiles/Sinkhorn.dir/TSinkhornKernel.cpp.s

Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornSolverBarycenter.cpp.o: Sinkhorn/CMakeFiles/Sinkhorn.dir/flags.make
Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornSolverBarycenter.cpp.o: /content/gdrive/MyDrive/Colab\ Notebooks/DomDecKeOps/lib/MultiScaleOT/src/Sinkhorn/TSinkhornSolverBarycenter.cpp
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir="/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/CMakeFiles" --progress-num=$(CMAKE_PROGRESS_3) "Building CXX object Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornSolverBarycenter.cpp.o"
	cd "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/Sinkhorn" && /usr/bin/c++  $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -o CMakeFiles/Sinkhorn.dir/TSinkhornSolverBarycenter.cpp.o -c "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/src/Sinkhorn/TSinkhornSolverBarycenter.cpp"

Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornSolverBarycenter.cpp.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing CXX source to CMakeFiles/Sinkhorn.dir/TSinkhornSolverBarycenter.cpp.i"
	cd "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/Sinkhorn" && /usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -E "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/src/Sinkhorn/TSinkhornSolverBarycenter.cpp" > CMakeFiles/Sinkhorn.dir/TSinkhornSolverBarycenter.cpp.i

Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornSolverBarycenter.cpp.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling CXX source to assembly CMakeFiles/Sinkhorn.dir/TSinkhornSolverBarycenter.cpp.s"
	cd "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/Sinkhorn" && /usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -S "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/src/Sinkhorn/TSinkhornSolverBarycenter.cpp" -o CMakeFiles/Sinkhorn.dir/TSinkhornSolverBarycenter.cpp.s

# Object files for target Sinkhorn
Sinkhorn_OBJECTS = \
"CMakeFiles/Sinkhorn.dir/TSinkhornSolver.cpp.o" \
"CMakeFiles/Sinkhorn.dir/TSinkhornKernel.cpp.o" \
"CMakeFiles/Sinkhorn.dir/TSinkhornSolverBarycenter.cpp.o"

# External object files for target Sinkhorn
Sinkhorn_EXTERNAL_OBJECTS =

Sinkhorn/libSinkhorn.a: Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornSolver.cpp.o
Sinkhorn/libSinkhorn.a: Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornKernel.cpp.o
Sinkhorn/libSinkhorn.a: Sinkhorn/CMakeFiles/Sinkhorn.dir/TSinkhornSolverBarycenter.cpp.o
Sinkhorn/libSinkhorn.a: Sinkhorn/CMakeFiles/Sinkhorn.dir/build.make
Sinkhorn/libSinkhorn.a: Sinkhorn/CMakeFiles/Sinkhorn.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir="/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/CMakeFiles" --progress-num=$(CMAKE_PROGRESS_4) "Linking CXX static library libSinkhorn.a"
	cd "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/Sinkhorn" && $(CMAKE_COMMAND) -P CMakeFiles/Sinkhorn.dir/cmake_clean_target.cmake
	cd "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/Sinkhorn" && $(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/Sinkhorn.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
Sinkhorn/CMakeFiles/Sinkhorn.dir/build: Sinkhorn/libSinkhorn.a

.PHONY : Sinkhorn/CMakeFiles/Sinkhorn.dir/build

Sinkhorn/CMakeFiles/Sinkhorn.dir/clean:
	cd "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/Sinkhorn" && $(CMAKE_COMMAND) -P CMakeFiles/Sinkhorn.dir/cmake_clean.cmake
.PHONY : Sinkhorn/CMakeFiles/Sinkhorn.dir/clean

Sinkhorn/CMakeFiles/Sinkhorn.dir/depend:
	cd "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build" && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/src" "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/src/Sinkhorn" "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build" "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/Sinkhorn" "/content/gdrive/MyDrive/Colab Notebooks/DomDecKeOps/lib/MultiScaleOT/build/Sinkhorn/CMakeFiles/Sinkhorn.dir/DependInfo.cmake" --color=$(COLOR)
.PHONY : Sinkhorn/CMakeFiles/Sinkhorn.dir/depend

