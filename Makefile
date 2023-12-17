default: build

build:
	@ make clean
	@ python build.py

draft:
	@ make clean
	@ python build.py --drafts

clean:
	@ rm -rf out
