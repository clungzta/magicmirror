# This only needs to be initially, for training the emotion recognition classifier
# A trained model is saved to file for magic mirror prediction

import os
import cv2
import numpy as np
import vision_utils
from random import shuffle
from collections import Counter
from sklearn.externals import joblib
from sklearn.model_selection import train_test_split

# Classifiers
from sklearn.svm import SVC
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis

import matplotlib.pyplot as plt
from sklearn.metrics import (brier_score_loss, precision_score, recall_score, f1_score)
from sklearn.calibration import CalibratedClassifierCV, calibration_curve

label_mapping = {0 : 'neutral',
                1 : 'anger',
                2 : 'contempt',
                3 : 'disgust',
                4 : 'fear',
                5 : 'happy',
                6 : 'sadness',
                7 : 'surprise'}

def load_data(datadir):

    X, y = [], []

    labels_path = os.path.join(datadir, 'labels')

    for dirpath, subdirs, files in os.walk(labels_path):
        for x in files:
            if x.endswith(".txt"):
                filepath = os.path.join(dirpath, x)
                print(filepath)

                with open(filepath) as file:  
                    label = label_mapping[int(file.read().split('.')[0][-1])]
                print(label)

                image_path = filepath.replace('labels', 'images').replace('_emotion.txt', '.png')

                img = cv2.imread(image_path)
                print(img.shape)

                X.append(vision_utils.get_face_landmarks(img)[0])
                y.append(label)

                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(img,'{}'.format(label),(20,80), font, 2,(255,0,255), 2,cv2.LINE_AA)
                cv2.imshow('img', img)
                cv2.waitKey(0)

    return X, y

# 327 labeled emotion images
X, y = load_data('/home/alex/Downloads/emotion_dataset/')

# print(X.shape, Counter(y))
clf = SVC(kernel='linear', probability=True, tol=1e-3)

accuracies = []
num_tests = 10
for i in range(num_tests):
    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)

    # Fit the model
    clf.fit(X_train, y_train)

    # Score the model
    accuracy = clf.score(X_test, y_test)
    print(accuracy)
    accuracies.append(accuracy)

    print("F1: {:.3f}".format(f1_score(y_test, clf.predict(X_test), average='weighted')))


joblib.dump(clf, 'emotion_classifier.pkl') 
print('Ran {} tests, mean: {:.2f}, std: {:.2f}'.format(num_tests, np.mean(accuracies), np.std(accuracies)))

# plt.show()