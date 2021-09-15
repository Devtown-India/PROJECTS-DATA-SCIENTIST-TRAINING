import numpy as np

class processing:
    def __init__(self, notes, vocab, features):
        self.notes = notes
        self.vocab = vocab
        self.sequence_len = features

    def prepare_test_sequences(self, pitches):
        # Creating the dictionary for mapping each note to the integer
        note_to_int = dict((note, number) for number, note in enumerate(pitches))

        # store the sequence for music generation
        test_inputs = []
        for i in range(0, len(self.notes) - self.sequence_len, 1):
            # randomly selecting the notes for prediction
            input_seq = self.notes[i: i + self.sequence_len]
            test_inputs.append([note_to_int[char] for char in input_seq])

        # reshape the data
        test_inputs = np.reshape(test_inputs, (len(test_inputs), self.sequence_len, 1))

        # normalization
        test_inputs = test_inputs / float(self.vocab)

        return test_inputs

    def notes_prediction(self, model, test_inputs, pitches, num_notes):
        """
        :param model: loaded generator model for prediction
        :param test_inputs: final inputs for music generation
        :param pitches: list of total unique notes
        :param num_notes: Number of notes to generate
        :return: predicted output
        """
        # start with a random integer
        initial = np.random.randint(0, len(test_inputs) - 1)

        # creating the dictionary for mapping each integer to a note
        int_to_note = dict((number, note) for number, note in enumerate(pitches))

        # pick a random sequence from the input for random start
        seq = list(test_inputs[initial])

        # store the final predicted audio notes
        output = []

        # generate num_notes notes one by one
        for note_index in range(num_notes):
            # reshape the data
            test = np.reshape(seq, (1, len(seq), 1))

            # normalization
            test = test / float(self.vocab)

            # call the generator model for prediction one by one
            pred = model.predict(test, verbose=0)

            # Predicted output index
            index = np.argmax(pred)

            # Mapping the predicted integer back to the corresponding note
            result = int_to_note[index]

            # Storing the predicted output
            output.append(result)

            # store next node (output) to the sequence
            seq.append([index])

            # remove the first note from the sequence
            seq.pop(0)

        return output

if __name__ == '__main__':
    print('generate_note')