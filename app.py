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

# Create a Flask application object
app = Flask(__name__)

# Start the debugger
app.config["DEBUG"] = True

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
    # audio_file_link = "https://melofyapi.blob.core.windows.net/melofy-api-input/twinkle_twinkle_little_star.wav"
    print("\n\naudio_file_link: " + audio_file_link)
    # working

    # Extract audio file name from audio_file_link
    audioFileName = audio_file_link.split('/')[-1]
    print("\n\nExtracted audio file name from audio_file_link")
    print("\naudioFileName: " + audioFileName)
    # working

    # Path to store audio file
    # pathToAudioFile = "C:\\Users\\aries\\Desktop\\melofy-api\\"
    pathToAudioFile = "/tmp"
    # working

    # Azure's Blob Connection string
    connectionString = "DefaultEndpointsProtocol=https;AccountName=melofyapi;AccountKey=ucqmEO03FyTs7/z9JS7pQkA7bIai7O0ycBs09Iataco8xk3BcxRDNmy5+NqYLqYjiMxTP8ZRRsaHFT4HRvn0Dw==;EndpointSuffix=core.windows.net"
    # working

    try:
        # Create the BlobServiceClient object which will be used to get blob
        blob_service_client = BlobServiceClient.from_connection_string(connectionString)
        print("\n\nCreated the BlobServiceClient object which will be used to get blob")
        # working

        # Set the container name
        input_container_name = "melofy-api-input"
        print("\n\nSet the container name")
        print("\n\ncontainer_name: " + input_container_name)
        # working

        # Create a blob client using the audioFileName as the name for the blob
        blob_client = blob_service_client.get_blob_client(container=input_container_name, blob=audioFileName)
        print("\n\nCreated a blob client using the audioFileName as the name for the blob")
        # working

        # Download the blob to pathToAudioFile
        download_file_path = os.path.join(pathToAudioFile, audioFileName)
        print("\n\nDownloading blob to \n\t" + download_file_path)
        # working

        with open(download_file_path, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())
        print("\n\nDownloaded the blob to \n\t" + download_file_path)
        # working

    except Exception as ex:
        print('Exception:')
        print(ex)

    # Generate converted audioFileName (name of audio file with .mid extension)
    # Extract all characters before . in audioFileName
    head, sep, tail = audioFileName.partition('.')
    print("\n\nExtracted all characters before . in audioFileName")
    # working

    # Concatenate filename with .mid extension
    convertedAudioFileName = head + ".mid"
    print("\n\nConcatenated filename with .mid extension")
    print("\nconvertedAudioFileName: " + convertedAudioFileName)
    # working

    # Command to convert WAV file to MIDI file
    command = "audio-to-midi --output " + convertedAudioFileName + " " + audioFileName
    # working

    # Execute the command
    stream = os.popen(command)
    # working

    # Display output of command
    output = stream.readlines()
    # working

    print("\n\nConverted WAV file to MIDI file")

    # Convert MIDI file to Note Sequence file
    audioNoteSequence = note_seq.midi_file_to_note_sequence(convertedAudioFileName)
    print("\n\nConverted MIDI file to Note Sequence file")
    # working

    # Initialize the basic_rnn model from Magenta
    bundle = sequence_generator_bundle.read_bundle_file('basic_rnn.mag')
    generator_map = melody_rnn_sequence_generator.get_generator_map()
    melody_rnn = generator_map['basic_rnn'](checkpoint=None, bundle=bundle)
    melody_rnn.initialize()
    print("\n\nInitialized the basic_rnn model from Magenta")
    # working

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
    # working

    # Generate file name for generated melody (MIDI)
    # Extract all characters before . in convertedAudioFileName
    head, sep, tail = convertedAudioFileName.partition('.')
    print("\n\nExtracted all characters before . in convertedAudioFileName")
    # working

    # Concatenate file name for generated melody with prefix gm- and .mid extension
    generatedMelody = "gm-" + head + ".mid"
    print("\n\nConcatenate file name for generated melody with prefix gm- and .mid extension")
    print("\ngeneratedMelody: " + generatedMelody)
    # working

    # Convert Note Sequence file to MIDI file
    note_seq.sequence_proto_to_midi_file(sequence, generatedMelody)
    print("\n\nConverted Note Sequence file to MIDI file")
    # working

    # Generate file name for generated melody (WAV)
    # Extract all characters before . in convertedAudioFileName
    head, sep, tail = generatedMelody.partition('.')
    print("\n\nExtracted all characters before . in generatedMelody")
    # working

    # Concatenate file name for generated melody with .wav extension
    convertedGeneratedMelody = head + ".wav"
    print("\n\nConcatenate file name for generated melody with .wav extension")
    print("\ngeneratedMelody: " + convertedGeneratedMelody)
    # working

    # Convert MIDI file to WAV file
    ps = Parser(generatedMelody)
    audio, player = play_notes(*ps.parse(), sawtooth, wait_done=False)
    wavfile.write(convertedGeneratedMelody, 44100, audio)
    print("\n\nConverted MIDI file to WAV file")
    # working

    # Upload generatedMelody to Azure Blob Storage Container
    try:
        # Create the BlobServiceClient object which will be used to upload blob
        blob_service_client = BlobServiceClient.from_connection_string(connectionString)
        print("\n\nCreated the BlobServiceClient object which will be used to get blob")
        # working

        # Set the container name
        output_container_name = "melofy-api-output"
        print("\n\nSet the container name")
        print("\n\ncontainer_name: " + output_container_name)
        # working

        # Create a blob client using the convertedGeneratedMelody as the name for the blob
        blob_client = blob_service_client.get_blob_client(container=output_container_name, blob=convertedGeneratedMelody)
        print("\n\nCreated a blob client using the convertedGeneratedMelody as the name for the blob")
        # working

        # Set path of file to upload
        upload_file_path = os.path.join(pathToAudioFile, convertedGeneratedMelody)
        # working

        # Create a blob client using the local file name as the name for the blob
        blob_client = blob_service_client.get_blob_client(container=output_container_name, blob=convertedGeneratedMelody)
        print("\n\nUploading to Azure Storage as blob:\n\t" + convertedGeneratedMelody)
        # working

        # Upload the created file
        with open(upload_file_path, "rb") as data:
            blob_client.upload_blob(data)
        print("\n\nUploaded to Azure Storage as blob:\n\t" + convertedGeneratedMelody)
        # working

    except Exception as ex:
        print('Exception:')
        print(ex)

    # Set link to uploaded audio file in Azure Blob Storage
    convertedGeneratedMelodyLink = "https://melofyapi.blob.core.windows.net/" + output_container_name + "/" + convertedGeneratedMelody

    return convertedGeneratedMelodyLink

# Run the application server
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug = True, host = '0.0.0.0')

# Example of correct POST request
# curl -i -X POST -H "Content-Type:application/json" -d "{\"audio_file_link\": \"https://melofyapi.blob.core.windows.net/melofy-api-input/twinkle_twinkle_little_star.wav\" }" http://localhost:5000/generate
# curl -i -X POST -H "Content-Type:application/json" -d "{\"audio_file_link\": \"https://melofyapi.blob.core.windows.net/melofy-api-input/twinkle_twinkle_little_star.wav\" }" https://melofy-api.herokuapp.com/generate