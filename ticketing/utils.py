import razorpay

def createRazorpayClient(id, key):
    return razorpay.Client(auth=(id, key))