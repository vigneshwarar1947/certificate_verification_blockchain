# certification/views.py
import hashlib
import json
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from .forms import CertificateForm, VerifyCertificateForm
from .models import Certificate
from web3 import Web3
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.urls import reverse




# Blockchain setup
blockchain_url = "http://127.0.0.1:8545"
w3 = Web3(Web3.HTTPProvider(blockchain_url))

if not w3.is_connected():
    raise ConnectionError("Web3 provider is not connected.")

try:
    with open('certification/contract_abi.json', 'r') as abi_file:
        abi_data = json.load(abi_file)
        contract_abi = abi_data.get("abi", [])
except Exception as e:
    raise ValueError(f"Error loading ABI file: {e}")

if not isinstance(contract_abi, list):
    raise TypeError("Contract ABI must be a list")

contract_address = Web3.to_checksum_address("0x6b77714ae74ceab026daa22830da5e3bf93ce5e4")
certificate_contract = w3.eth.contract(address=contract_address, abi=contract_abi)

if w3.eth.accounts:
    default_account = w3.eth.accounts[0]
    w3.eth.default_account = default_account
else:
    raise ValueError("No Ethereum accounts found.")

def compute_file_hash(file):
    sha256 = hashlib.sha256()
    for chunk in file.chunks():
        sha256.update(chunk)
    return "0x" + sha256.hexdigest()

def home(request):
    return render(request, 'certification/home.html')


# Hardcoded credentials
HARDCODED_USERNAME = "admin"
HARDCODED_PASSWORD = "1234"

def institute_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username == HARDCODED_USERNAME and password == HARDCODED_PASSWORD:
            request.session['authenticated_institute'] = True
            return redirect('submit_certificate')
        else:
            messages.error(request, "Invalid credentials")

    return render(request, 'certification/institute_login.html')



def submit_certificate(request):
    if not request.session.get('authenticated_institute'):
        return redirect('institute_login')

    if request.method == 'POST':
        form = CertificateForm(request.POST, request.FILES)
        if form.is_valid():
            student_name = form.cleaned_data['student_name']
            certificate_file = form.cleaned_data['certificate_file']
            file_hash = compute_file_hash(certificate_file)

            try:
                tx_hash = certificate_contract.functions.storeCertificate(
                    bytes.fromhex(file_hash[2:])
                ).transact({'from': default_account})

                w3.eth.wait_for_transaction_receipt(tx_hash)

            except Exception as e:
                messages.error(request, f"Blockchain transaction failed: {e}")
                return render(request, 'certification/certificate_form.html', {'form': form})

            Certificate.objects.create(
                student_name=student_name,
                certificate_file=certificate_file,
                certificate_hash=file_hash,
                blockchain_tx=tx_hash.hex()
            )
            messages.success(request, "Certificate stored successfully!")
            return redirect('certificate_success')


    else:
        form = CertificateForm()

    return render(request, 'certification/certificate_form.html', {'form': form})


def verify_certificate(request):
    if request.method == 'POST':
        form = VerifyCertificateForm(request.POST, request.FILES)
        if form.is_valid():
            certificate_file = form.cleaned_data['certificate_file']
            file_hash = compute_file_hash(certificate_file)

            try:
                exists = certificate_contract.functions.verifyCertificate(
                    bytes.fromhex(file_hash[2:])
                ).call()
            except Exception as e:
                messages.error(request, f"Blockchain error: {e}")
                return render(request, 'certification/verify_certificate.html', {'form': form})

            if exists:
                

                return redirect(f"{reverse('certificate_verified')}?valid=yes")

            else:
                return redirect(f"{reverse('certificate_verified')}?valid=no")


    else:
        form = VerifyCertificateForm()
    return render(request, 'certification/verify_certificate.html', {'form': form})
def institute_logout(request):
    request.session.flush()
    return redirect('home')
def certificate_success(request):
    return render(request, 'certification/certificate_success.html')
def certificate_verified(request):
    result = request.GET.get('valid', '')
    return render(request, 'certification/certificate_verified.html', {'result': result})

