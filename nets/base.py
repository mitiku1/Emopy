from keras.layers  import Input, Flatten, Dense, Conv2D, MaxPooling2D, Dropout
from keras.models import Sequential,Model, model_from_json

from train_config import LEARNING_RATE,EPOCHS,BATCH_SIZE,DATA_SET_DIR,LOG_DIR,STEPS_PER_EPOCH

from test_config import MODEL_PATH
import os
import keras
import numpy as np
from loggers.base import EmopyLogger
import time
from util import SevenEmotionsClassifier
from config import IMG_SIZE





class NeuralNet(object):
    """
    Base class for all neural nets.

    Parameters
    ----------
    input_shape : tuple
    
    """
    
    def __init__(self,input_shape,learning_rate,batch_size,epochs,steps_per_epoch,preprocessor = None,logger=None,train=True):
        self.input_shape = input_shape
        assert len(input_shape) == 3, "Input shape of neural network should be length of 3. e.g (48,48,1)" 
    
        self.preprocessor = preprocessor

        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.steps_per_epoch = steps_per_epoch
        
        self.logger = logger
        self.feature_extractors = ["image"]
        self.number_of_class = self.preprocessor.classifier.get_num_class()
        if train:
            # self.model = self.build()
            self.model = self.load_model("models/nn/nn-16")
        else:
            self.model = self.load_model(MODEL_PATH)


    def build(self):
        """
        Build neural network model
        
        Returns 
        -------
        keras.models.Model : 
            neural network model
        """
        model = Sequential()
        model.add(Conv2D(32, kernel_size=(3, 3), activation='relu', padding= "same", input_shape=self.input_shape,kernel_initializer="glorot_normal"))
        # model.add(Dropout(0.2))
        model.add(Conv2D(64, (3, 3), activation='relu',padding= "same",kernel_initializer="glorot_normal"))

        model.add(Dropout(0.2))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Conv2D(64, (3, 3), activation='relu',padding= "same",kernel_initializer="glorot_normal"))
        model.add(Dropout(0.2))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Conv2D(128, (3, 3), activation='relu',padding= "same",kernel_initializer="glorot_normal"))
        model.add(Dropout(0.2))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Conv2D(252, (3, 3), activation='relu',padding= "same",kernel_initializer="glorot_normal"))
        model.add(Dropout(0.2))

        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Flatten())
        model.add(Dense(252, activation='relu'))
        model.add(Dropout(0.2))
        model.add(Dense(1024, activation='relu'))
        model.add(Dropout(0.2))
        model.add(Dense(self.number_of_class, activation='softmax'))
        
        self.built = True
        return model

    def load_model(self,model_path):
        with open(model_path+".json") as model_file:
            model = model_from_json(model_file.read())
            model.load_weights(model_path+".h5")
            return model
        
    def save_model(self,args):
        """
        Saves NeuralNet model. The naming convention is for json and h5 files is,
        `/path-to-models/model-local-folder-model-number.json` and  
        `/path-to-models/model-local-folder-model-number.h5` respectively.
        This method also increments model_number inside "model_number.txt" file.
        """
        parent,model_file = os.path.split(args.model_path)
        if not os.path.exists(parent):
            if args.verbose:
                print("Model save path directory does not exits. Creating "+str(parent)+" directory")
            os.makedirs(parent)
        if os.path.exists(args.model_path+".json") and args.verbose:
            print "model with name '"+ os.path.exists(args.model_path+".json") +"' already exists, the model file will be replaced."
        if os.path.exists(args.model_path+".h5") and args.verbose:
            print "model with name '"+ os.path.exists(args.model_path+".h5") +"' already exists, the model file will be replaced."
       
        if not os.path.exists(os.path.join(parent,"model_number.txt")):
            model_number = np.array([0])
        else:
            model_number = np.fromfile(os.path.join(parent,"model_number.txt"),dtype=int)
        model_file_name = model_file+"-"+str(model_number[0])
        with open(os.path.join(parent,model_file_name+".json"),"a+") as jfile:
            jfile.write(self.model.to_json())
        self.model.save_weights(os.path.join(parent,model_file_name+".h5"))
        model_number[0]+=1
        model_number.tofile(os.path.join(parent,"model_number.txt"))

    def train(self,args):
        """Traines the neuralnet model.      
        This method requires the following two directory to exist
        /PATH-TO-DATASET-DIR/train
        /PATH-TO-DATASET-DIR/test
        
        """
        
        
        self.model.compile(loss=keras.losses.categorical_crossentropy,

                    optimizer=keras.optimizers.Adam(args.lr),

                    metrics=['accuracy'])
        self.model.summary()
        # self.model.fit(x_train,y_train,epochs = EPOCHS, 
        #                 batch_size = BATCH_SIZE,validation_data=(x_test,y_test))
        self.preprocessor = self.preprocessor(args.dataset_path)
        self.model.fit_generator(self.preprocessor.flow(),steps_per_epoch=args.steps,
                        epochs=args.epochs,
                        validation_data=(self.preprocessor.test_images, self.preprocessor.test_image_emotions))
        score = self.model.evaluate(self.preprocessor.test_images, self.preprocessor.test_image_emotions)
        self.save_model(args)
        self.logger.log_model(args, score,None)

    def predict(self,face):
        # assert face.shape == IMG_SIZE, "Face image size should be "+str(IMG_SIZE)
        face = face.reshape(-1,48,48,1)
        face = face.astype(np.float32)/255
        emotions = self.model.predict(face)
        return emotions