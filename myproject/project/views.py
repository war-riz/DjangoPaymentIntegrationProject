from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
import paypalrestsdk
from django.conf import settings
from paypalrestsdk import Payment
from django.core.mail import send_mail
import boto3


# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('PaymentsTable')


# Create views here
def home(request):

    if request.method == "POST":
        # Redirect to a success page or another view
        return redirect('create_payment')  # Named URL
    
    return render(request, 'home.html')


# Configure PayPal SDK
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})



def create_payment(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        meeting_date = request.POST.get('meeting_date')
        meeting_time = request.POST.get('meeting_time')
        user_email = request.POST.get('email')

        payment = Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "transactions": [{
                "amount": {
                    "total": amount,
                    "currency": "USD"
                },
                "description": "Meeting payment",
            }],
            "redirect_urls": {
                "return_url": request.build_absolute_uri('/payment/success/'),
                "cancel_url": request.build_absolute_uri('/payment/cancel/')
            }
        })

        if payment.create():
            approval_url = next(link.href for link in payment.links if link.rel == "approval_url")
            return redirect(approval_url)
        else:
            return JsonResponse({'error': 'Payment creation failed'}, status=500)

    return render(request, 'payment_form.html')  # A form for collecting payment details




def execute_payment(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    payment = Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        # Save payment details to DynamoDB
        payment_data = {
            'payment_id': payment.id,
            'amount': payment.transactions[0].amount.total,
            'currency': payment.transactions[0].amount.currency,
            'status': payment.state,
            'user_email': payment.payer.payer_info.email,
            'timestamp': payment.create_time,
        }
        table.put_item(Item=payment_data)

        # Send email confirmation
        # send_confirmation_email(payment.payer.payer_info.email, payment_data)

        return render(request, 'payment_success.html', {'message': "Payment successful!"})
    else:
        return render(request, 'payment_failure.html', {'message': "Payment failed!"})


# Send Confirmation Email

# def send_confirmation_email(user_email, payment_data):
#     subject = "Payment Confirmation"
#     message = f"""
#     Thank you for your payment!
    
#     Payment Receipt:
#     - Amount: ${payment_data['amount']}
#     - Currency: {payment_data['currency']}
#     - Transaction ID: {payment_data['payment_id']}
    
#     Meeting Details:
#     - Date: [Add meeting date here]
#     - Time: [Add meeting time here]

#     Next Steps:
#     - You will receive a calendar invite shortly.
#     - Please prepare for your meeting at the scheduled time.

#     Regards,
#     Your Team
#     """

#     send_mail(
#         subject,
#         message,
#         settings.DEFAULT_FROM_EMAIL,
#         [user_email],
#         fail_silently=False,
#     )


def payment_failure(request):
    return render(request, 'payment_failure.html', {'message': "Payment failed. Please try again."})



def payment_cancel(request):
    return render(request, 'payment_cancel.html', {'message': "Payment was canceled."})
