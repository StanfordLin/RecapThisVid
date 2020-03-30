import os
import nltk
from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance
import numpy as np
import networkx as nx
from datetime import datetime

from google.cloud import videointelligence
from pytube import YouTube
from google.cloud import storage



# paragraph = "Calgary remains the centre of the province’s coronavirus outbreak, with 378 (61 per cent) of Alberta’s case coming in the AHS Calgary zone, including 325 cases within Calgary’s city limits. The Edmonton zone has 22 per cent of cases, the second-most in the province. More than 42,500 Albertans have now been tested for COVID-19, meaning nearly one in every 100 Albertans have received a test. About 1.5 per cent of those tests have come back positive. Rates of testing in Alberta jolted back up on Friday, with more than 3,600 conducted — the most yet in a single day. The surge followed one of Alberta’s lowest testing days Thursday, as the province shifted its testing focus away from returning travellers and towards health-care workers and vulnerable populations, including those in hospital or living in continuing care facilities."
# user journey -> submit url -> download video from url -> transcribe video -> use text rank to build summary

def download_and_save_video(url):
    print("Downloading youtube video...")
    # videoFile = YouTube(url).streams.get_highest_resolution().download(filename='Analyze', output_path='~/tmp')
    
    storageCli = storage.Client()
    # get bucket
    bucket = storageCli.get_bucket('videos12491')
    blob = bucket.blob('Analyze.mp4')
    
    # TODO: Fix this error of AttributeError: 'str' object has no attribute 'tell', needs to save in /tmp file in google cloud function
    # blob.upload_from_filename('Analyze.mp4')

    blob.upload_from_filename(YouTube(url).streams.get_highest_resolution().download(filename='Analyze', output_path='/tmp'))
    print("Uploaded to cloud bucket.")

def transcribe_video(url):
    startTime = datetime.now()
    """Transcribe speech from a video stored on GCS."""
    video_client = videointelligence.VideoIntelligenceServiceClient()
    features = [videointelligence.enums.Feature.SPEECH_TRANSCRIPTION]

    config = videointelligence.types.SpeechTranscriptionConfig(
        language_code="en-US", enable_automatic_punctuation=True
    )
    video_context = videointelligence.types.VideoContext(
        speech_transcription_config=config
    )
    operation = video_client.annotate_video(
        "gs://videos12491/Analyze.mp4", features=features, video_context=video_context
    )

    print("\nProcessing video for speech transcription...")

    result = operation.result(timeout=3000)

    # There is only one annotation_result since only
    # one video is processed.
    annotation_results = result.annotation_results[0]
    wallOfText = ""
    for speech_transcription in annotation_results.speech_transcriptions:
        # print(speech_transcription)

        # The number of alternatives for each transcription is limited by
        # SpeechTranscriptionConfig.max_alternatives.
        # Each alternative is a different possible transcription
        # and has its own confidence score.
        for alternative in speech_transcription.alternatives:
            wallOfText += alternative.transcript
            # print("Alternative level information:")

            # print("Transcript: {}".format(alternative.transcript))
            # print("Confidence: {}\n".format(alternative.confidence))

            # print("Word level information:")
            # for word_info in alternative.words:
            #     word = word_info.word
            #     start_time = word_info.start_time
            #     end_time = word_info.end_time
            #     print(
            #         "\t{}s - {}s: {}".format(
            #             start_time.seconds + start_time.nanos * 1e-9,
            #             end_time.seconds + end_time.nanos * 1e-9,
            #             word,
            #         )
            #     )
    return wallOfText
 
    # print(f"""Execution Time: {datetime.now() - startTime}""")


#paragraph = f.read()

def transcribe_get_all(url):
    startTime = datetime.now()
    """Transcribe speech from a video stored on GCS."""
    video_client = videointelligence.VideoIntelligenceServiceClient()
    features = [videointelligence.enums.Feature.SPEECH_TRANSCRIPTION]

    config = videointelligence.types.SpeechTranscriptionConfig(
        language_code="en-US", enable_automatic_punctuation=True
    )
    video_context = videointelligence.types.VideoContext(
        speech_transcription_config=config
    )

    operation = video_client.annotate_video(
        "gs://videos12491/trimmed.mp4", features=features, video_context=video_context
    )

    print("\nProcessing video for speech transcription.")

    result = operation.result(timeout=3000)

    # There is only one annotation_result since only
    # one video is processed.
    annotation_results = result.annotation_results[0]
    for speech_transcription in annotation_results.speech_transcriptions:
        # print(speech_transcription)

        # The number of alternatives for each transcription is limited by
        # SpeechTranscriptionConfig.max_alternatives.
        # Each alternative is a different possible transcription
        # and has its own confidence score.
        for alternative in speech_transcription.alternatives:
            print("Alternative level information:")

            print("Transcript: {}".format(alternative.transcript))
            print("Confidence: {}\n".format(alternative.confidence))

            print("Word level information:")
            for word_info in alternative.words:
                word = word_info.word
                start_time = word_info.start_time
                end_time = word_info.end_time
                print(
                    "\t{}s - {}s: {}".format(
                        start_time.seconds + start_time.nanos * 1e-9,
                        end_time.seconds + end_time.nanos * 1e-9,
                        word,
                    )
                )
    # print(f"""Execution Time: {datetime.now() - startTime}""")

def split_text_into_sentences(paragraph):
    sentences = paragraph.split(". ")
    #print(sentences)
    return text_preprocessing(sentences)

def text_preprocessing(sentences):
    clean_sentences = []
    for sentence in sentences:
        clean_sentences.append(sentence.replace("[^a-zA-Z]", " ").split(" "))
    clean_sentences.pop() # getting rid of the empty list at the end

    return clean_sentences

def compare_sentences(sentence1, sentence2):
    stop_words = set(stopwords.words('english'))
    # make a list of all the unique words between the two sentences
    # make a vector holds how each word has a specific entity in the list
    # from the vector, use cosine_distance to find how different these vectors are

    sentence1 = [sentence.lower() for sentence in sentence1]
    sentence2 = [sentence.lower() for sentence in sentence2]

    all_unique_words = list(set(sentence1+sentence2)) # get a list of all unique words

    vector1 = [0]*len(all_unique_words)
    vector2 = [0]*len(all_unique_words)

    for i in sentence1: # each time there is a non-stop word, count its occurence
        if i in stop_words: # skip if it is a stopword
            continue
        vector1[all_unique_words.index(i)] += 1

    for i in sentence2:
        if i in stop_words: # skip if it is a stopword
            continue
        vector2[all_unique_words.index(i)] += 1

    # https://kite.com/python/docs/nltk.cluster.cosine_distance
    # cosine similarity is a mathematical term used to compute the angle between two documents where each word is on it's own dimension
    # cosine distance is 1-cosine_similarity, below we are calculating cosine similarity
    return 1 - cosine_distance(vector1, vector2)

def build_similarity_matrix(sentences):
    # go through and a build a matrix that is sentences.length by sentences.length
    similarity_matrix = np.zeros((len(sentences), len(sentences)))
    
    for counter1, sentence1 in enumerate(sentences):
        for counter2, sentence2 in enumerate(sentences):
            if sentence1 == sentence2:
                continue
            similarity_matrix[counter1][counter2] = compare_sentences(sentence1, sentence2)
    
    return similarity_matrix

def generate_summary(paragraph):
    nltk.download('stopwords')
    print("Finished Download, going to generate summary")
    # generate the sentences from the existing paragraph
    sentences = split_text_into_sentences(paragraph)
    
    # generate a similarity matrix
    similarity_matrix = build_similarity_matrix(sentences)
    #print(similarity_matrix)

    # rank the sentences in the similarity matrix
    sentence_similarity_graph = nx.from_numpy_array(similarity_matrix)
    scores = nx.pagerank(sentence_similarity_graph)

    # organize the scores from top to bottom
    ranked_sentence = sorted(((scores[i],s) for i,s in enumerate(sentences)), reverse=True)    
    #print("Indexes of top ranked_sentence order are ", ranked_sentence)     

    summarize_text = []

    for i in range(min(5, len(sentences))):
      summarize_text.append(" ".join(ranked_sentence[i][1]))

    # Step 5 - Offcourse, output the summarize text
    summary = ". ".join(summarize_text)+"."
    #print("Summarize Text: \n", summary)
    return summary

if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=XlL0_m675_4"
    # transcribe_get_all(url)
    #download_and_save_video('https://youtu.be/9bZkp7q19f0')
    # print(transcribe_video(url))
    generate_summary("each otherfor so longWe know the game and we're gonna play.")
    # print("Paragraph summarized: " + paragraph)