const useShipping = document.querySelector('#use-shipping');
const clearBtn = document.querySelector('.clear-btn');

const shippingForm = document.querySelector('#shipping-info');
const billingForm = document.querySelector('#billing-info');
const creditForm = document.querySelector('#credit-info');
const placeOrderBtn = document.querySelector('#place-order');

const shippingArray = Array.from(shippingForm);
const billingArray = Array.from(billingForm);

// Stripe varibles for global scope
let stripe;
let elements;
let cardNumber;
let cardExpiry;
let cardCvc;

// Stripe style appearance


document.addEventListener('DOMContentLoaded', function () {
    stripe = Stripe('pk_test_51Rh10IH0alBtp0wTyuOyuvMEZ2GNtrSJqFNsaM8BWKNIcHs7n4Bfil4U7G8YIhet0QkUuGnzdTYUFYkrdi5s9nVB00fVfyLW9e');
    

    elements = stripe.elements();

    // Create individual elements with same appearance
    cardNumber = elements.create('cardNumber', {
        placeholder: '1234 1234 1234 1234',
        style: {
            base: {
                iconColor: '#c4f0ff',
                color: '#fff',
                fontSize: '1rem',
                fontSmoothing: 'antialiased',
                border: '1px solid red',
                ':-webkit-autofill': {
                    color: '#fce883',
                },
                '::placeholder': {
                    color: '#6c757d',
                },
            },
            invalid: {
                iconColor: '#FFC7EE',
                color: '#FFC7EE',
            },
        }
    });

    cardExpiry = elements.create('cardExpiry', {
        placeholder: 'MM/YY',
        //style: elementStyles
    });

    cardCvc = elements.create('cardCvc', {
        placeholder: 'CVC',
        //style: elementStyles
    });

    // Mount each element to its container
    cardNumber.mount('#card-number');
    cardExpiry.mount('#card-expiry');
    cardCvc.mount('#card-cvc');

    // Handle real-time validation errors from the card Element
    cardNumber.on('change', function(event) {
        displayStripeErrors('cardNumber', event.error ? event.error.message : '');
    });

    cardExpiry.on('change', function(event) {
        displayStripeErrors('cardExpiry', event.error ? event.error.message : '');
    });

    cardCvc.on('change', function(event) {
        displayStripeErrors('cardCvc', event.error ? event.error.message : '');
    });

});

// Function to display Stripe errors
function displayStripeErrors(message) {
    // If no fieldType provided, clear all errors
    if (!fieldType) {
        document.querySelectorAll('[id$="-error"').forEach(el => {
            el.textContent = '';
            el.style.display = 'none';
        });
        // Also clear general errors
        const generalErrorElement = document.getElementById('card-errors');
        if (generalErrorElement) {
            generalErrorElement.textContent = "";
            generalErrorElement.style.display = "none";
        }
        return;
    }

    // Display error for specific field
    const errorElement = document.getElementById(`${fieldType}-error`);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = message ? 'block' : 'none';
    }

    // Also display in general card erros div for fallback
    const generalErrorElement = document.getElementById('card-errors');
    if (generalErrorElement) {
        if (message) {
            generalErrorElement.textContent = message;
            generalErrorElement.style.display = 'block';
        } else {
            // Only clear general errors if no other field has errors
            const hasErrors = Array.from(document.querySelectorAll('[id$="-error"]')).some(el => el.textContent.trim());
            if (!hasErrors) {
                generalErrorElement.textContent = "";
                generalErrorElement.style.display = "none";
            }
        }
    }
}

// Duplicates the shipping info to the billing info
function copyShippingInput() {
    if (useShipping.checked == true) {
        let counter = 0;
        billingArray.forEach(input => {
            if (input.type == "text" || input.type == "select-one") {
                input.value = shippingArray[counter].value;
                counter++;
            }
        });
    } else {
        billingArray.forEach(input => {
            if (input.type == "text" || input.type == "select-one") {
                input.value = "";
            }
        })
    }
}

// Submits data to web2py for validation
async function submitData(e) {
    e.preventDefault();

    // Disable button during processing
    this.disabled = true;

    // delete any existing error messages
    const allErrors = document.querySelectorAll(".error")
    allErrors.forEach(span => span.remove());

    displayStripeErrors("");

    try {
        // First make sure that if use shipping is checked, we are getting that data!
        copyShippingInput();
        
        // 1. Validate Stripe card first
        const {token, error} = await stripe.createToken(cardNumber);

        if (error) {
            displayStripeErrors('cardNumber', error.message);
            this.disabled = false;
            return;
        }

        // 2. Gather form data
        const allForms = document.querySelectorAll('.order-forms');
        let allFormsData = {};
        allForms.forEach(form => {
            let formId = form.id;
            eachFormData = new FormData(form);
            let objectData = {};
            eachFormData.forEach((value, key) => {
                objectData[key] = value;
            });
            allFormsData[formId] = objectData
        });

        // 3. Add Stripe token to the data
        allFormsData['stripe_token'] = token.id;

        // 4. send ajax request
        jQuery.ajax({
            url: 'checkout',
            type: 'POST',
            data: JSON.stringify(allFormsData),
            contentType: 'application/json',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            success: function (response) {
                response = JSON.parse(response)

                if (response.status === 'success') {
                    window.location.href = response.redirect_url
                }

                else if (response.status === 'error') {
                    // Check for stripe specific errors
                    if (response.stripe_error) {
                        displayStripeErrors('cardNumber', response.stripe_error);
                    }
                    
                    if (response.errors) {
                        // iterates through response.errors and adds error message for each one
                        for (const formName in response.errors) {
                            const currentForm = document.querySelector(`#${formName}`);
                            Object.entries(response.errors[formName]).forEach(
                                ([inputName, errorMessage]) => {
                                    const errorSpan = document.createElement("span");
                                    errorSpan.classList.add("error", "text-danger");
                                    errorSpan.textContent = errorMessage;
                                    const currentInput = currentForm.querySelector(`[name="${inputName}"]`);
                                    currentInput.parentElement.appendChild(errorSpan)
                                }
                            );
                        }
                    }
    
                    // UPDATE THE FORMKEY VALUES IN THE DOM
                    if (response.new_keys) {
                        for (const formName in response.new_keys) {
                            const currentForm = document.querySelector(`#${formName}`);
                            if (currentForm) {
                                const formKeyInput = currentForm.querySelector('[name="_formkey"]');
                                if (formKeyInput) {
                                    formKeyInput.value = response.new_keys[formName];
                                }
                            }
                        }
                    }
                } // #END IF RESPONSE.STATUS === ERROR
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error("AJAX Error:", textStatus, errorThrown, jqXHR.responseText);
                alert("An error occurred during submission.");
                // Consider displaying a general error message on the page if the AJAX call itself fails
            }
        });
    } catch (error) {
        console.error('Error:', error);
        displayStripeErrors('cardNumber','An error occurred processing your payment. Please try again.');
    } finally {
        this.disabled = false;
    }
    return false;
}


// EVENT LISTENERS
placeOrderBtn.addEventListener('click', submitData);
useShipping.addEventListener('change', copyShippingInput);
document.addEventListener("DOMContentLoaded", () => copyShippingInput());


