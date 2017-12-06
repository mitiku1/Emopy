from __future__ import print_function
import os
from sklearn.utils import shuffle
import numpy as np
import cv2
import dlib


class Preprocessor(object):
    """"Base class for preprocessors.
    Preprocessing includes reading and sanitizing dataset.
    
    parameters
    ---------
    input_shape : tuple
        shape of input images to generate
    classifier : util.Classifier
        classifier used for classifying emotions
    batch_size : int
        batch size for generating batch of images
    """
    
    def __init__(self,classifier, input_shape = None,batch_size=32,verbose = True):
        self.classifier = classifier
        self.input_shape = input_shape
        self.batch_size = batch_size
        self.called = False
        self.verbose = verbose
    """Preprocess given path
    
    parameters
    ----------
    path    : str
        path to directory containing training and test directory.
    """
    
    def __call__(self,path):
        assert os.path.exists(path),"Specified dataset directory '"+path+"' does not exist "
        train_test_dir = os.listdir(path)
        assert "train" in train_test_dir , "Specified dataset directory '"+path+"' does not  contain train directory." 
        assert "test" in train_test_dir , "Specified dataset directory '"+path+"' does not  contain test directory." 
        self.train_image_paths = []
        self.train_image_emotions = []
        for emdir in os.listdir(os.path.join(path,"train")):
            print("Loading ",os.path.join(path,"train",emdir))
            for img_file in os.listdir(os.path.join(path,"train",emdir)):
                self.train_image_paths.append(os.path.join(path,"train",emdir,img_file))
                self.train_image_emotions.append(self.classifier.get_class(emdir))
        self.test_image_paths = []
        self.test_image_emotions = []
        for emdir in os.listdir(os.path.join(path,"test")):
            print("Loading ",os.path.join(path,"test",emdir))
            for img_file in os.listdir(os.path.join(path,"test",emdir)):
                self.test_image_paths.append(os.path.join(path,"test",emdir,img_file))
                self.test_image_emotions.append(self.classifier.get_class(emdir))
        self.called = True
        assert len(self.train_image_emotions) == len(self.train_image_paths), "number of train inputs are not equal to train labels"
        assert len(self.test_image_emotions) == len(self.test_image_paths), "number of test inputs are not equal to test labels"
        
        self.train_image_emotions = np.array(self.train_image_emotions)
        self.train_image_paths = np.array(self.train_image_paths)
        self.test_images = self.get_images(self.test_image_paths).reshape(-1,self.input_shape[0],self.input_shape[1],self.input_shape[2])
        self.test_image_emotions = np.eye(self.classifier.get_num_class()) [np.array(self.test_image_emotions)]

        return self
    def generate_indexes(self,random=True):
        indexes = range(len(self.train_image_emotions))
        if (random):
            indexes = shuffle(indexes)
        indexes = np.array(indexes)
        return indexes
    def flow(self):
        assert self.called, "Preprocessor should be called with path of dataset first to use flow method."
        while True:
            indexes = self.generate_indexes(True)
            for i in range(0,len(indexes) - self.batch_size,self.batch_size):
                current_indexes = indexes[i:i+self.batch_size]
                current_paths = self.train_image_paths[current_indexes]
                current_emotions = self.train_image_emotions[current_indexes]
                current_images = self.get_images(current_paths).reshape(-1,self.input_shape[0],self.input_shape[1],self.input_shape[2])
                current_emotions = np.eye(self.classifier.get_num_class())[current_emotions]
                yield current_images,current_emotions
    
    def sanitize(self,image):
        if image is None:
            raise "Unable to sanitize None image"
        if len(image.shape)>2:
            image = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        image = cv2.resize(image,(self.input_shape[0],self.input_shape[1]))
        return image
    
    
    def get_images(self,paths):
        output = np.zeros(shape=(len(paths),self.input_shape[0],self.input_shape[1]),dtype=float)
        for i in range(len(paths)):
            img = cv2.imread(paths[i])
            img = self.sanitize(img)
            output[i] = img
        return output
    
    def get_faces(self,frame,detector):
        faces = detector(frame)
        output = []
        rectangles =[]
        for face in faces:
            top = max(0,face.top())
            left = max(0,face.left())
            bottom = min(frame.shape[0],face.bottom())
            right = min(frame.shape[1],face.right())
            rectangles.append(dlib.rectangle(left,top,right,bottom));
            output.append(frame[top:bottom, left:right])
        return output,rectangles