import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # it remove all the tensorflow warnings

import pickle
from glob import glob
import tensorflow as tf
from data_lit import Data_Augmentiaion
from music21 import converter, instrument, note, chord

''' Install the data '''
# Fetch the data by glob which is use to retrieve the file pathname
file = glob('midi/*.mid')
song = file[:24] # number of items in the file

# use to collect the notes contain in all 24 files
notes = []

# collecting the notes data from each song file
for data in song:
    # converting .mid data file to stream object which make easy to handle the data
    # stream object is another type of file object
    midi = converter.parse(data)

    try:
        # Given a single stream, partition into a part for each unique instrument
        parts = instrument.partitionByInstrument(midi)
    except:
        # if there is no instrument
        pass

    # if parts has instrument parts like violen, Piano....... etc.
    if parts:
        notes_to_parse = parts.parts[0].recurse()
    else:
        notes_to_parse = midi.flat.notes

    for element in notes_to_parse:
        # it return True if object is of specific type as note.Note
        # Notes like G4, E4, F#4 .......etc
        if isinstance(element, note.Note):
            # if element is a note, it extract the pitch
            notes.append(str(element.pitch))

        # it return True if object is of specific type as chord.Chord
        # Chords like 3.4.5, 2.3 .........etc
        elif isinstance(element, chord.Chord):
            # if element is a chord, append the normal form of the
            # chord (a list of integers) to the list of notes.
            notes.append('.'.join(str(n) for n in element.normalOrder))

''' Save the notes '''
# Save the notes of instrument of given midi
with open('notes', 'wb') as handle:
    pickle.dump(notes, handle)

# defining the vocabulary size (set defined for unique values)
vocab = len(set(notes))

''' Get the train and label dataset '''
dataset = Data_Augmentiaion(features=100)
train, label = dataset.prepare_train_sequences(notes, vocab)

''' Initializing the Training Model '''

# LSTM (Long short term memory) Model
# recurrent neural network model
model = tf.keras.Sequential([
            tf.keras.layers.LSTM(128, return_sequences=True),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.LSTM(128, return_sequences=True),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(256, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(vocab, activation='softmax')
        ])

model.compile(loss=tf.keras.losses.CategoricalCrossentropy(from_logits=False), optimizer='adam', metrics=['accuracy'])

model.fit(train, label, epochs=30, verbose=1, batch_size=32)

''' save the model '''
model.save_weights('generator/')