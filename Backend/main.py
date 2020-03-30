from flask import escape
from google.cloud import videointelligence
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import Credentials
from google.cloud import pubsub_v1
import VideoIntelligence

SendGridAPIKey = Credentials.SendGridAPIKey
error_count = 0
project_id = "videoml-lahacks"
topic_name = "testTopic"

def hello_http(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
    """
    # request_json = request.get_json(silent=True)
    # request_args = request.args
    # print("THE REQUEST{}").format(request)
    # print("the request_json{}".format(escape(request_json)))

    # if request_json and 'url' and 'email' in request_json:
    #     url = request_json['url']
    #     email = request_json['email']
    # elif request_args and 'url' in request_args:
    #     url = request_args['url']
    #     email = request_json['email']
    # else:
    #     url = 'World'
    # print("The URL {}".format(escape(url)))
    # print("The email {}".format(escape(email)))
    email=request.form.get('email')
    url=request.form.get('url')
    print(f'Your youtube link {email} is being downloaded. Results will be sent to {url}')
    publish_messages_with_custom_attributes(project_id,topic_name)
    return f'Your youtube link {url} is being downloaded. Results will be sent to {email}'

def transcribeYT(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
    """
    # request_json = request.get_json(silent=True)
    # request_args = request.args

    # if request_json and 'url' in request_json:
    #     url = request_json['url']
    # elif request_args and 'url' in request_args:
    #     url = request_args['url']
    # else:
    #     url = 'World'
    email=request.form.get('email')
    url=request.form.get('url')
    print(f'Email: {email} Youtube Link: {url}...')
      # Pub Sub
    publisher = pubsub_v1.PublisherClient()
    # The `topic_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/topics/{topic_name}`
    topic_path = publisher.topic_path(project_id, topic_name)
    data = "Message for Transcription to Begin".encode("utf-8")
    publisher.publish(topic_path, data, youtubeUrl=url.encode("utf-8")).result()
    return f'Your youtube link {url} is being downloaded. Results will be sent to {email}'

def hello_pubsub(event, context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         event (dict):  The dictionary with data specific to this type of
         event. The `data` field contains the PubsubMessage message. The
         `attributes` field will contain custom attributes if there are any.
         context (google.cloud.functions.Context): The Cloud Functions event
         metadata. The `event_id` field contains the Pub/Sub message ID. The
         `timestamp` field contains the publish time.
    """
    import base64

    print("""This Function was triggered by messageId {} published at {}
    """.format(context.event_id, context.timestamp))
    subscriber = pubsub_v1.SubscriberClient()

    email = ""
    url = ""
    print("Callback was called")
    def callback(message):
        print("Received message: {}".format(message.data))
        if message.attributes:
            print("Attributes:")
            for key in message.attributes:
                if(key == "url"):
                    url = message.attributes.get(key)
                elif (key == "email"):
                    email = message.attributes.get(key)
                else:
                    value = message.attributes.get(key)
                    print("{}: {}".format(key, value))
                
        message.ack()

    subscription_path = subscriber.subscription_path(
        project_id, "testTopicSubscription"
    )

    future = subscriber.subscribe(subscription_path, callback)
    future.result()

    print(f'Pub Sub Email: {email} Youtube Link: {url}...')
    generatedSummary = VideoIntelligence.transcribe_video(url)
    print("Video Intelligence API Initiated")
    # # TODO: Parameterize the email
    formulate_message("stanlin1999@gmail.com","The summary for your video {}: {}".format(url,generatedSummary),"Summary of your video")

def formulate_message(email, message, url):
    email = Mail(
        from_email='nihalpot@gmail.com',
        to_emails=email,
        subject=('A summary of the following video: '+str(url)),
        html_content='<strong>'+message+'</strong>') 
    return send_email(email)

def send_email(email):
    global error_count
    try:
        sg = SendGridAPIClient(SendGridAPIKey) # create the sendgrid client
        # print out the http response code and characteristics
        response = sg.send(email) 
        print(response.status_code)

        if response.status_code != 202: # retry three times until this works
            if error_count < 3:
                error_count = error_count+1
                send_email(email)
            else:
                return "Failure."

        return "Success."
    except Exception as e:
        print(e)
        if error_count < 3:
            error_count = error_count+1
            send_email(email)
        return "Failure."