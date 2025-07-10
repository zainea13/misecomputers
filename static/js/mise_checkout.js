const useShipping = document.querySelector('#use-shipping');
const clearBtn = document.querySelector('.clear-btn');

const shippingForm = document.querySelector('#shipping-info');
const billingForm = document.querySelector('#billing-info');

const placeOrderBtn = document.querySelector('#place-order');

const shippingArray = Array.from(shippingForm.elements); // #added .elements, may screw things up
const billingArray = Array.from(billingForm.elements);

// disable scrolling if overlay exists
const loadingScreen = document.querySelector('.loading-screen');
if (loadingScreen.style.display == 'block') {
    document.body.style.overflow = 'hidden';
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
        // console.log('z1=Validating payment element...');
        const { error: paymentError } = await elements.submit();

        // Don't return here - we want to collect ALL errors first
        
        if (paymentError) {
            // DEBUG
            // console.log('z2=Payment element has errors:', paymentError);
            displayStripeErrors(paymentError.message);
            ajaxCompleted = true; // Mark AJAX as complete
        }

        // 2. Gather form data
        const allForms = document.querySelectorAll('.order-forms');
        let allFormsData = {};
        allForms.forEach(form => {
            let formId = form.id;
            // DEBUG
            // console.log('z3=Processing form:', formId);
            const eachFormData = new FormData(form);
            let objectData = {};
            eachFormData.forEach((value, key) => {
                objectData[key] = value;
            });
            allFormsData[formId] = objectData;
            // DEBUG
            // console.log('z4=Form data for', formId, ':', objectData);
        });

        // Add a flag to indicate this is just validation
        allFormsData['validate_only'] = true;
        allFormsData['payment_success'] = paymentError ? false : true;

        // DEBUG
        // console.log('z5=All forms data:', allFormsData);

        // DEBUG
        // console.log('z6=Validating forms...');

        // Send validation request
        const validationResponse = await new Promise((resolve, reject) => {
            jQuery.ajax({
                url: 'checkout',
                type: 'POST',
                data: JSON.stringify(allFormsData),
                contentType: 'application/json',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                success: resolve,
                error: reject
            });
        });
        // DEBUG
        // console.log('z7=Validation response: ', validationResponse);

        try {
            parsedValidationResponse = JSON.parse(validationResponse);
        } catch (parseError) {
            // DEBUG
            // console.error('z8=Error parsing validation response:', parseError);
            displayStripeErrors('Invalid response from server');
            return;
        }

        // DEBUG
        // console.log('z9=Parsed validation response: ', parsedValidationResponse);


        // 3. Check if we have form errors
        let hasFormErrors = false;
        if (parsedValidationResponse.status === 'error') {
            // DEBUG
            // console.log('z10=Form validation failed:', parsedValidationResponse);
            hasFormErrors = true;

            if (parsedValidationResponse.errors) {
                // DEBUG
                // console.log("z11=in the form error part");
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
        
        if (parsedValidationResponse.status === 'error' || paymentError) {
            // DEBUG
            // console.log("z12=in the IF WITH THE OR ");
            // console.log("z13=parsedValidationResponse.new_keys:", parsedValidationResponse.new_keys);

            // Update form keys
            if (parsedValidationResponse.new_keys) {
                
                for (const formName in parsedValidationResponse.new_keys) {
                    const currentForm = document.querySelector(`#${formName}`);
                    if (currentForm) {
                        const formKeyInput = currentForm.querySelector('[name="_formkey"]');
                        if (formKeyInput) {
                            // DEBUG
                            // console.log(`z14=new form key for form: ${formName}, Key: ${parsedValidationResponse.new_keys[formName]}`);
                            formKeyInput.value = parsedValidationResponse.new_keys[formName];
                        }
                    }
                }
            }
        }

        // 4. If we have EITHER payment errors OR form errors, stop here
        if (paymentError || hasFormErrors) {
            // DEBUG
            // console.log('z15=Validation failed - Payment error:', !!paymentError, 'Form errors:', hasFormErrors);

            return; // Stop here, don't process payment
        }

        // 5. ONLY IF BOTH VALIDATIONS PASSED - Process payment
        if (parsedValidationResponse.status === 'validation_success') {
            // DEBUG
            // console.log('z16=Both form and payment validation passed, processing payment...');
            // console.log('z17=Parsed validation response: ', parsedValidationResponse);

            const { error, paymentIntent } = await stripe.confirmPayment({
                elements,
                confirmParams: {
                    return_url: window.location.origin + '/thankyou'
                },
                redirect: 'if_required'
            });

            // DEBUG
            // console.error('z17.5=Payment Intent:', paymentIntent);

            if (error) {
                // DEBUG
                // console.error('z18=Payment confirmation error:', error);
                displayStripeErrors(error.message);
                return;
            }

            if (paymentIntent.status !== 'succeeded') {
                displayStripeErrors('Payment was not successful. Please try again.');
                return;
            }

            // DEBUG
            // console.log('z19=Payment confirmed successfully:', paymentIntent);

            // 6. FINAL STEP - Submit everything to complete the order
            allFormsData['payment_intent_id'] = paymentIntent.id;
            allFormsData['validate_only'] = false; // Now we want to complete the order

            // DEBUG
            // console.log('z20=Finalizing order...');

            jQuery.ajax({
                url: 'checkout',
                type: 'POST',
                data: JSON.stringify(allFormsData),
                contentType: 'application/json',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                success: function (response) {
                    // DEBUG
                    // console.log('z21=Final response:', response);
                    ajaxCompleted = true; // Mark AJAX as complete

                    // DEBUG
                    try {
                        response = JSON.parse(response);
                        // DEBUG
                        // console.log('z22=Parsed response:', response);
                    } catch (parseError) {
                        // DEBUG
                        // console.error('z23=Error parsing final response:', parseError);
                        displayStripeErrors('Invalid response from server');
                        return;
                    }

                    if (response.status === 'success') {
                        localStorage.setItem('order_success', true);
                        window.location.href = response.redirect_url;
                    } else {
                        // Handle any final errors
                        if (response.stripe_error) {
                            displayStripeErrors(response.stripe_error);
                        } else {
                            displayStripeErrors('An error occurred completing your order.');
                        }
                    }
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    console.error("z23=AJAX Error:", textStatus, errorThrown);
                    displayStripeErrors("An error occurred completing your order. Please try again.");
                    ajaxCompleted = true; // Mark AJAX as complete
                }
            });
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


// debug function for seeing form keys
// const formKeyShow = document.querySelector('[name="_formkey"]');
// formKeyShow.setAttribute('type','text');
// formKeyShow.style.width = '100%';
// formKeyShow.parentElement.style.display = "block";


// EVENT LISTENERS
placeOrderBtn.addEventListener('click', submitData);
useShipping.addEventListener('change', copyShippingInput);
document.addEventListener("DOMContentLoaded", () => copyShippingInput());


