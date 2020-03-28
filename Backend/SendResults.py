# we will be sending out the results through this file
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SendGridAPIKey = "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"
error_count = 0

def formulate_message(email, message, url):
    email = Mail(
        from_email='nihalpot@gmail.com',
        to_emails=email,
        subject=('A summary of the following video: '+str(url)),
        html_content='<strong>'+message+'</strong>')
    send_email(email)

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

if __name__ == "__main__":
    formulate_message("nihalpot2002@gmail.com","Test","https://www.twilio.com/docs/studio/tutorials/how-to-send-appointment-reminders")