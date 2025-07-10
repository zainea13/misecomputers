const useShipping = document.querySelector('#use-shipping');
const clearBtn = document.querySelector('.clear-btn');

const shippingForm = document.querySelector('#shipping-info');
const billingForm = document.querySelector('#billing-info');

const placeOrderBtn = document.querySelector('#place-order');

const shippingArray = Array.from(shippingForm.elements);
const billingArray = Array.from(billingForm.elements);

// disable scrolling if overlay exists
const loadingScreen = document.querySelector('.loading-screen');
if (loadingScreen.style.display == 'block') {
    document.body.style.overflow = 'hidden';
}


// use shipping checkbox stuff
document.querySelector('#use-shipping').addEventListener('change', function() {
    const target = document.querySelector('#billing-info');
    const collapse = new bootstrap.Collapse(target, { toggle: false });
    
    if (this.checked) {
        collapse.hide();
    } else {
        collapse.show();
    }
});

function handleToggle(event) {
    if (event.target === event.currentTarget) {
        const checkbox = document.querySelector('#use-shipping');
        checkbox.checked = !checkbox.checked;
        checkbox.dispatchEvent(new Event('change'));
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



// Stripe varibles for global scope
let stripe;
let elements;
let paymentElement;
let clientSecret;


document.addEventListener('DOMContentLoaded', function () {
    stripe = Stripe('pk_test_51Rh10IH0alBtp0wTyuOyuvMEZ2GNtrSJqFNsaM8BWKNIcHs7n4Bfil4U7G8YIhet0QkUuGnzdTYUFYkrdi5s9nVB00fVfyLW9e');   // Initialize payment element
    inititializePaymentElement();
});

// Intialize Payment element
async function inititializePaymentElement() {
    try {
        // Create payment intent on the server
        const response = await fetch('create_payment_intent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const data = await response.json();

        if (data.error) {
            displayStripeErrors(data.error);
            return;
        }

        clientSecret = data.client_secret;
        // DEBUG
        // console.log('Current clientSecret:', clientSecret);

        const appearance = {
            // labels: 'floating',  THIS IS SO COOOOOL, BUT NO
            rules: {
                '.Label': {
                    fontSize: '1rem',
                    marginBottom: '.5rem'
                },
                '.Input': {
                    // marginBottom: '1rem'
                },
                '.Input:focus': {
                    borderColor: '#80bdff'
                },
                '.Input::placeholder': {
                    color: '#dddddd'
                },
            },
            theme: 'stripe',
            variables: {
                // fontSize: '16px',
                borderRadius: '.25rem',
                gridRowSpacing: '1.5rem'
            }

        };

        const options = {
            layout: {
                type: 'tabs',
                defaultCollapsed: false,
            }
        };


        // Create Elements instance
        elements = stripe.elements({ clientSecret, appearance, custom_text: {} });

        // Create Payment element
        paymentElement = elements.create('payment', options);
        paymentElement.mount('#payment-element');

        // Check if form is loaded
        paymentElement.on('ready', () => {
            loadingScreen.style.display = 'none';
            document.body.style.overflow = 'visible';
        });

        // Handle validation errors
        paymentElement.on('change', function (event) {
            displayStripeErrors(event.error ? event.error.message : '');
        });

    } catch (error) {
        console.error('Error initializing Payment Element:', error);
        displayStripeErrors('Failed to initialize payment form. Please refresh the page.');
    }
}

// Function to display Stripe errors
function displayStripeErrors(message) {
    const errorElement = document.getElementById('payment-errors');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = message ? 'block' : 'none';
    }
}

// Add this function to handle redirect returns
async function handleStripeRedirectReturn() {
    const urlParams = new URLSearchParams(window.location.search);
    const paymentIntentClientSecret = urlParams.get('payment_intent_client_secret');
    const paymentIntentId = urlParams.get('payment_intent');
    
    if (paymentIntentClientSecret) {
        console.log('Handling Stripe redirect return...');
        
        try {
            // Retrieve the payment intent to check its status
            const { paymentIntent, error } = await stripe.retrievePaymentIntent(paymentIntentClientSecret);
            
            if (error) {
                console.error('Error retrieving payment intent:', error);
                displayStripeErrors(error.message);
                return;
            }
            
            console.log('Payment Intent Status:', paymentIntent.status);
            
            if (paymentIntent.status === 'succeeded') {
                // Payment was successful, now complete the order
                await completeOrderAfterPayment(paymentIntent.id);
            } else if (paymentIntent.status === 'requires_action') {
                // Payment requires additional action
                displayStripeErrors('Payment requires additional action. Please try again.');
            } else {
                // Payment failed or was cancelled
                displayStripeErrors('Payment was not successful. Please try again.');
            }
            
        } catch (error) {
            console.error('Error handling redirect return:', error);
            displayStripeErrors('An error occurred processing your payment. Please try again.');
        }
    }
}

// New function to complete the order after successful payment
async function completeOrderAfterPayment(paymentIntentId) {
    try {
        // Get the form data that was stored or reconstruct it
        // You'll need to either store this data or reconstruct it
        const allForms = document.querySelectorAll('.order-forms');
        let allFormsData = {};
        
        allForms.forEach(form => {
            let formId = form.id;
            const eachFormData = new FormData(form);
            let objectData = {};
            eachFormData.forEach((value, key) => {
                objectData[key] = value;
            });
            allFormsData[formId] = objectData;
        });
        
        // Add payment information
        allFormsData['payment_intent_id'] = paymentIntentId;
        allFormsData['validate_only'] = false;
        
        console.log('Completing order with payment intent:', paymentIntentId);
        
        // Submit the final order
        const response = await fetch('checkout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(allFormsData)
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            localStorage.setItem('order_success', true);
            window.location.href = data.redirect_url;
        } else {
            displayStripeErrors(data.stripe_error || 'An error occurred completing your order.');
        }
        
    } catch (error) {
        console.error('Error completing order:', error);
        displayStripeErrors('An error occurred completing your order. Please try again.');
    }
}


// Submits data to web2py for validation
async function submitData(e) {
    e.preventDefault();

    // Disable button during processing
    this.disabled = true;
    this.textContent = 'Processing...';

    // delete any existing error messages
    const allErrors = document.querySelectorAll(".error")
    const inputErrors = document.querySelectorAll('.input-error')
    allErrors.forEach(span => span.remove());
    inputErrors.forEach(err => err.classList.remove('input-error'));
    
    displayStripeErrors("");
    
    let ajaxCompleted;
    let parsedValidationResponse;

    try {
        // First make sure that if use shipping is checked, we are getting that data!
        copyShippingInput();

        // Clear any previous error states
        displayStripeErrors("");

        // 1. Validate Stripe payment element (but don't stop on errors)
        // DEBUG
        console.log('z1=Validating payment element...');
        const { error: paymentError } = await elements.submit();

        // Don't return here - we want to collect ALL errors first
        
        if (paymentError) {
            // DEBUG
            console.log('z2=Payment element has errors:', paymentError);
            displayStripeErrors(paymentError.message);
            ajaxCompleted = true; // Mark AJAX as complete
        }

        // 2. Gather form data
        const allForms = document.querySelectorAll('.order-forms');
        let allFormsData = {};
        allForms.forEach(form => {
            let formId = form.id;
            // DEBUG
            console.log('z3=Processing form:', formId);
            const eachFormData = new FormData(form);
            let objectData = {};
            eachFormData.forEach((value, key) => {
                objectData[key] = value;
            });
            allFormsData[formId] = objectData;
            // DEBUG
            console.log('z4=Form data for', formId, ':', objectData);
        });

        // Add a flag to indicate this is just validation
        allFormsData['validate_only'] = true;
        allFormsData['payment_validation_success'] = paymentError ? false : true;

        // DEBUG
        console.log('z5=All forms data:', allFormsData);

        // DEBUG
        console.log('z6=Validating forms...');

        // Send validation request
        const validationResponse = await fetch('checkout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(allFormsData)
        });

        const validationData = await validationResponse.json();
        parsedValidationResponse = validationData;

        // 3. Check if we have form errors
        let hasFormErrors = false;
        if (parsedValidationResponse.status === 'error') {
            // DEBUG
            console.log('z10=Form validation failed:', parsedValidationResponse);
            hasFormErrors = true;

            if (parsedValidationResponse.errors) {
                // DEBUG
                console.log("z11=in the form error part");
                // Display form errors
                for (const formName in parsedValidationResponse.errors) {
                    const currentForm = document.querySelector(`#${formName}`);
                    Object.entries(parsedValidationResponse.errors[formName]).forEach(
                        ([inputName, errorMessage]) => {
                            const errorSpan = document.createElement("span");
                            errorSpan.classList.add("error", "text-danger");
                            errorSpan.textContent = errorMessage;
                            const currentInput = currentForm.querySelector(`[name="${inputName}"]`);
                            if (currentInput && currentInput.parentElement) {
                                currentInput.classList.add('input-error');
                                currentInput.parentElement.appendChild(errorSpan);
                            }
                        }
                    );
                }
            }
        } 
        
        // Update form keys if provided
        if (parsedValidationResponse.new_keys) {
            
            for (const formName in parsedValidationResponse.new_keys) {
                const currentForm = document.querySelector(`#${formName}`);
                if (currentForm) {
                    const formKeyInput = currentForm.querySelector('[name="_formkey"]');
                    if (formKeyInput) {
                        // DEBUG
                        console.log(`z14=new form key for form: ${formName}, Key: ${parsedValidationResponse.new_keys[formName]}`);
                        formKeyInput.value = parsedValidationResponse.new_keys[formName];
                    }
                }
            }
        }
        

        // 4. If we have EITHER payment errors OR form errors, stop here
        if (paymentError || hasFormErrors) {
            // DEBUG
            console.log('z15=Validation failed - Payment error:', !!paymentError, 'Form errors:', hasFormErrors);

            return; // Stop here, don't process payment
        }

        // 5. ONLY IF BOTH VALIDATIONS PASSED - Process payment
        if (parsedValidationResponse.status === 'validation_success') {
            console.log('Both form and payment validation passed, processing payment...');

            // Store form data in sessionStorage for redirect-based payments
            sessionStorage.setItem('checkout_form_data', JSON.stringify(allFormsData));

            const { error, paymentIntent } = await stripe.confirmPayment({
                elements,
                confirmParams: {
                    return_url: window.location.href // Return to the same page
                }
                // Remove redirect: 'if_required' to always allow redirects
            });

            if (error) {
                // DEBUG
                console.error('z18=Payment confirmation error:', error);
                displayStripeErrors(error.message);

                // Update form keys
                if (parsedValidationResponse.new_keys) {
                    for (const formName in parsedValidationResponse.new_keys) {
                        const currentForm = document.querySelector(`#${formName}`);
                        if (currentForm) {
                            const formKeyInput = currentForm.querySelector('[name="_formkey"]');
                            if (formKeyInput) {
                                // DEBUG
                                console.log(`z14-2=new form key for form: ${formName}, Key: ${parsedValidationResponse.new_keys[formName]}`);
                                formKeyInput.value = parsedValidationResponse.new_keys[formName];
                            }
                        }
                    }
                }

                this.disabled = false;
                this.textContent = 'Place Order';
                return;
            }

            // If we get here without a redirect, the payment was processed without redirect
            if (paymentIntent && paymentIntent.status === 'succeeded') {
                console.log('Payment confirmed successfully without redirect:', paymentIntent);
                await completeOrderAfterPayment(paymentIntent.id);
            }
        }

    } catch (error) {
        console.error('z24=Caught error:', error);
        displayStripeErrors('An error occurred processing your order. Please try again.');
    } finally {
        // Only reset button if AJAX is complete or no AJAX was sent (e.g., due to validation errors)
        if (ajaxCompleted || !(parsedValidationResponse?.status === 'validation_success')) {
            this.disabled = false;
            this.textContent = 'Place Order';
        }
    }
    return false;
}

// Update the DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', function () {
    stripe = Stripe('pk_test_51Rh10IH0alBtp0wTyuOyuvMEZ2GNtrSJqFNsaM8BWKNIcHs7n4Bfil4U7G8YIhet0QkUuGnzdTYUFYkrdi5s9nVB00fVfyLW9e');
    
    // Check if we're returning from a payment redirect
    handleStripeRedirectReturn();
    
    // Initialize payment element
    inititializePaymentElement();
});

// Update the completeOrderAfterPayment function to use stored data if available
async function completeOrderAfterPayment(paymentIntentId) {
    try {
        let allFormsData;
        
        // Try to get stored form data first
        const storedData = sessionStorage.getItem('checkout_form_data');
        if (storedData) {
            allFormsData = JSON.parse(storedData);
            sessionStorage.removeItem('checkout_form_data'); // Clean up
        } else {
            // Fallback: reconstruct from current form state
            const allForms = document.querySelectorAll('.order-forms');
            allFormsData = {};
            
            allForms.forEach(form => {
                let formId = form.id;
                const eachFormData = new FormData(form);
                let objectData = {};
                eachFormData.forEach((value, key) => {
                    objectData[key] = value;
                });
                allFormsData[formId] = objectData;
            });
        }
        
        // Add payment information
        allFormsData['payment_intent_id'] = paymentIntentId;
        allFormsData['validate_only'] = false;
        
        console.log('Completing order with payment intent:', paymentIntentId);
        
        // Submit the final order
        const response = await fetch('checkout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(allFormsData)
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            localStorage.setItem('order_success', true);
            window.location.href = data.redirect_url;
        } else {
            displayStripeErrors(data.stripe_error || 'An error occurred completing your order.');
        }
        
    } catch (error) {
        console.error('Error completing order:', error);
        displayStripeErrors('An error occurred completing your order. Please try again.');
    }
}

// debug function for seeing form keys
// const formKeyShow = document.querySelector('[name="_formkey"]');
// formKeyShow.setAttribute('type','text');
// formKeyShow.style.width = '100%';
// formKeyShow.parentElement.style.display = "block";


// EVENT LISTENERS
placeOrderBtn.addEventListener('click', submitData);
useShipping.addEventListener('change', copyShippingInput);
document.addEventListener("DOMContentLoaded", () => copyShippingInput());


