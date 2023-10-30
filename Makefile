default: build

build:
	@ make clean
	@ python build.py

clean:
	@ rm -rf out
