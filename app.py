# Import libraries
from flask import Flask
from flask import request
import os, uuid
import requests
import magenta
import note_seq
import tensorflow
import numpy as np
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from magenta.models.melody_rnn import melody_rnn_sequence_generator
from magenta.models.shared import sequence_generator_bundle
from note_seq.protobuf import generator_pb2
from note_seq.protobuf import music_pb2
from timidity import Parser, play_notes
from scipy.signal import square, sawtooth
from scipy.io import wavfile
from google.cloud import storage

# Create a Flask application object
app = Flask(__name__)

# Explicitly use Google Cloud service account credentials by specifying the private key file
storage_client = storage.Client.from_service_account_json('melofy-1b47c-33e8fbb61207.json')

# Start the debugger
app.config["DEBUG"] = True

# Initialize the basic_rnn model from Magenta
bundle = sequence_generator_bundle.read_bundle_file('basic_rnn.mag')
generator_map = melody_rnn_sequence_generator.get_generator_map()
melody_rnn = generator_map['basic_rnn'](checkpoint=None, bundle=bundle)
melody_rnn.initialize()
print("\n\nInitialized the basic_rnn model from Magenta")

# A route to return the homepage
@app.route('/', methods=['GET'])
def home():
    return '''<h1>Generate Melody API</h1>
<p>An API for generating melody from supplied audio file link.</p>'''

# A route to 404 page
@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404

# A route to generate melody from supplied audio file link
@app.route('/generate', methods=['POST'])
def generate_melody():
    # If there is no request data in json or audio_file item in request data
    # Abort the request and return error code 400
    if not request.json or not 'audio_file_link' in request.json:
        abort(400)

    # Retrieve audio file link from request.json
    audio_file_link = request.json['audio_file_link']
    print("\n\naudio_file_link: " + audio_file_link)

    # Extract audio file name from audio_file_link
    audioFileName = audio_file_link.split('/')[-1]
    print("\n\nExtracted audio file name from audio_file_link")
    print("\naudioFileName: " + audioFileName)

    # Path to store audio file
    # Get current working directory
    # This is the path where you run the flask app
    pathToAudioFile = os.getcwd()
    print("\n\nCurrent working directory: " + pathToAudioFile)

    # Append input folder to end of path to store audio file
    inputFolder = "input"
    pathToAudioFile = pathToAudioFile + "\\" + inputFolder

    # Azure's Blob Connection string
    connectionString = ("DefaultEndpointsProtocol=https;"
                        "AccountName=melofyapi;"
                        "AccountKey=ucqmEO03FyTs7/z9JS7pQkA7bIai7O0ycBs09Iataco8xk3BcxR"
                        "DNmy5+NqYLqYjiMxTP8ZRRsaHFT4HRvn0Dw==;"
                        "EndpointSuffix=core.windows.net")

    try:
        # Create the BlobServiceClient object which will be used to get blob
        blob_service_client = BlobServiceClient.from_connection_string(connectionString)
        print("\n\nCreated the BlobServiceClient object which will be used to get blob")

        # Set the container name
        input_container_name = "melofy-api-input"
        print("\n\nSet the container name")
        print("\n\ncontainer_name: " + input_container_name)

        # Create a blob client using the audioFileName as the name for the blob
        blob_client = blob_service_client.get_blob_client(container=input_container_name, blob=audioFileName)
        print("\n\nCreated a blob client using the audioFileName as the name for the blob")

        # Set path to store download file
        download_file_path = os.path.join(pathToAudioFile, audioFileName)
        print("\n\nDownloading blob to \n\t" + download_file_path)

        # Download the blob to pathToAudioFile
        with open(download_file_path, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())
        print("\n\nDownloaded the blob to \n\t" + download_file_path)

    except Exception as ex:
        print('Exception:')
        print(ex)

    # Generate converted audioFileName (name of audio file with .mid extension)
    # Extract all characters before . in audioFileName
    head, sep, tail = audioFileName.partition('.')
    print("\n\nExtracted all characters before . in audioFileName")

    # Concatenate filename with .mid extension
    convertedAudioFileName = head + ".mid"
    print("\n\nConcatenated filename with .mid extension")
    print("\nconvertedAudioFileName: " + convertedAudioFileName)

    # Command to convert WAV file to MIDI file
    command = "audio-to-midi --output " + inputFolder + "\\" + convertedAudioFileName + " " + inputFolder + "\\" + audioFileName 

    # Execute the command
    stream = os.popen(command)

    # Display output of command
    output = stream.readlines()

    print("\n\nConverted WAV file to MIDI file")

    # Convert MIDI file to Note Sequence file
    audioNoteSequence = note_seq.midi_file_to_note_sequence(inputFolder + "\\" + convertedAudioFileName)
    print("\n\nConverted MIDI file to Note Sequence file")

    # Model options
    input_sequence = audioNoteSequence
    num_steps = 128
    temperature = 1.0

    # Set the start time to begin on the next step after the last note ends
    last_end_time = (max(n.end_time for n in input_sequence.notes)
                    if input_sequence.notes else 0)
    qpm = input_sequence.tempos[0].qpm 
    seconds_per_step = 60.0 / qpm / melody_rnn.steps_per_quarter
    total_seconds = num_steps * seconds_per_step

    generator_options = generator_pb2.GeneratorOptions()
    generator_options.args['temperature'].float_value = temperature
    generate_section = generator_options.generate_sections.add(
    start_time=last_end_time + seconds_per_step,
    end_time=total_seconds)

    # Ask the model to continue the sequence
    sequence = melody_rnn.generate(input_sequence, generator_options)
    print("\n\nGenerated melody from audio file")

    # Generate file name for generated melody (MIDI)
    # Extract all characters before . in convertedAudioFileName
    head, sep, tail = convertedAudioFileName.partition('.')
    print("\n\nExtracted all characters before . in convertedAudioFileName")

    # Concatenate file name for generated melody with prefix gm- and .mid extension
    generatedMelody = "gm-" + head + ".mid"
    print("\n\nConcatenate file name for generated melody with prefix gm- and .mid extension")
    print("\ngeneratedMelody: " + generatedMelody)

    # Convert Note Sequence file to MIDI file
    note_seq.sequence_proto_to_midi_file(sequence, inputFolder + "\\" + generatedMelody)
    print("\n\nConverted Note Sequence file to MIDI file")

    # Currently, no conversion from MIDI to WAV file will be executed
    # This is because the WAV file produces a high pitch sound that's not favourable to ears
    # Generate file name for generated melody (WAV)
    # Extract all characters before . in convertedAudioFileName
    head, sep, tail = generatedMelody.partition('.')
    print("\n\nExtracted all characters before . in generatedMelody")

    # Concatenate file name for generated melody with .wav extension
    convertedGeneratedMelody = head + ".wav"
    print("\n\nConcatenate file name for generated melody with .wav extension")
    print("\ngeneratedMelody: " + convertedGeneratedMelody)

    # Convert MIDI file to WAV file
    ps = Parser(inputFolder + "\\" + generatedMelody)
    audio, player = play_notes(*ps.parse(), sawtooth, wait_done=False)
    wavfile.write(inputFolder + "\\" + convertedGeneratedMelody, 44100, audio)
    print("\n\nConverted MIDI file to WAV file")

    # Upload generatedMelody to Firebase Cloud Storage
    try:
        # The ID of your Google Cloud S bucket
        bucket_name = "melofy-1b47c.appspot.com"

        # The path to your file to upload
        source_file_name = inputFolder + "\\" + convertedGeneratedMelody

        # The ID of your GCS object
        destination_blob_name = convertedGeneratedMelody

        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(source_file_name)

        print(
            "File {} uploaded to {}.".format(
                source_file_name, destination_blob_name
            )
        )

    except Exception as ex:
        print('Exception:')
        print(ex)

    return convertedGeneratedMelody

# Run the application server
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host = '0.0.0.0')