import tensorflow as tf
import numpy as np
import cv2





## reading the image and resizing for the model

image = cv2.imread('img_align_celeba/img_align_celeba/000007.jpg')

image = cv2.resize(image,(150,150))

image = np.array(image)

image = image.reshape(1,150,150,3)



## loading the saved model.h5 file
model = tf.keras.models.load_model('model.h5')



##  Predicting the one hot encoding as the output
dict  = {1: 'Male', 0: 'Female'}
out_arr = model.predict(image)[0]
print(out_arr)
## converting the one hot encoding to the class output
print(f'Predicted class is : {dict[np.argmax(out_arr)]}')