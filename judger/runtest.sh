rm -rf build && mkdir build && cd build && cmake .. && make && make install
cd ../bindings/Python && rm -rf build && python3 setup.py install || exit 1
cd ../../tests/Python_and_core
python3 test.py
