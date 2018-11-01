# this will create the run directory before mount
# and also copy the default checker

mkdir -p run/data run/sub run/log run/sub/defaultspj
cp lib/defaultspj.cpp run/sub/defaultspj/foo.cc
cd run/sub/defaultspj
echo cpp > LANG
g++ -o foo foo.cc -O2 -std=c++11 -lm

# then run the following command to launch the docker
# sudo docker run -d -p 5000:5000 -v /path/to/your/run/:/ejudge/run <imageName>
