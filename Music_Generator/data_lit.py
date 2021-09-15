import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # it remove all the tensorflow warnings

import numpy as np
import tensorflow as tf

class Data_Augmentiaion:
    def __init__(self, features):
        # length of the feature vector
       self.sequence_len = features

    def prepare_train_sequences(self, notes, vocab):
        """
        :param notes: These are the collected nodes
        :param vocab: vocabulary size of the notes
        :return: training_input and label dataset
        """
        # Extract the unique pitches or notes from the list of notes.
        pitches = sorted(set(notes))

        # Create a dictionary to map notes to integers
        note_to_int = dict((note, number) for number, note in enumerate(pitches))

        # to store the input and label for training
        inputs = []
        label = []

        # create input sequences and the corresponding label
        for i in range(0, len(notes) - self.sequence_len, 1):
            input_seq = notes[i: i + self.sequence_len]
            output_seq = notes[i + self.sequence_len]
            inputs.append([note_to_int[char] for char in input_seq])
            label.append(note_to_int[output_seq])

        # reshape the input
        inputs = np.reshape(inputs, (len(inputs), self.sequence_len, 1))

        # normalization
        inputs = inputs / float(vocab)

        # one hot binary encoding the output label vector
        label = tf.keras.utils.to_categorical(label)

        return inputs, label

if __name__ == '__main__':
    print('data_lit')
