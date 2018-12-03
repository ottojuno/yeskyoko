# fetch predictor
curl -O http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bzip2 -d shape_predictor_68_face_landmarks.dat.bz2

# save into etc
mkdir -p etc
mv shape_predictor_68_face_landmarks.dat etc