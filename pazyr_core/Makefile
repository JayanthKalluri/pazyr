build-core:
	uv build
ifeq ($(OS),Windows_NT)
	if not exist ..\packages mkdir ..\packages
	copy dist\*.whl ..\packages
	del /Q dist\*.*
else
	mkdir -p ../packages
	cp dist/*.whl ../packages/
	rm -rf dist
endif
