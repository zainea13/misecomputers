const useShipping = document.querySelector('#use-shipping');
const clearBtn = document.querySelector('.clear-btn');

const shippingForm = document.querySelector('#shipping-info');
const billingForm = document.querySelector('#billing-info');
const creditForm = document.querySelector('#credit-info');
const placeOrderBtn = document.querySelector('#place-order');

const shippingArray = Array.from(shippingForm.elements); 
const billingArray = Array.from(billingForm.elements);

// Stripe varibles for global scope
let stripe;
let elements;
let card;


document.addEventListener('DOMContentLoaded', function () {
    stripe = Stripe('pk_test_51Rh10IH0alBtp0wTyuOyuvMEZ2GNtrSJqFNsaM8BWKNIcHs7n4Bfil4U7G8YIhet0QkUuGnzdTYUFYkrdi5s9nVB00fVfyLW9e');
    elements = stripe.elements();

    const style = {
        base: {
            color: '#32325d',
            fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
            fontSmoothing: 'antialiased',
            fontSize: '16px',
            '::placeholder': {
                color: '#aab7c4'
            }
        },
        invalid: {
            color: '#fa755a',
            iconColor: '#fa755a'
        }
    };
    card = elements.create('card', {style: style});
    
    card.mount('#card-element');

    // Handle real-time validation errors from the card Element
    card.on('change', function(event) {
        displayStripeErrors(event.error ? event.error.message : '');
    });

});

// Function to display Stripe errors
function displayStripeErrors(message) {
    const errorElement = document.getElementById('card-errors');
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

    // delete any existing error messages
    const allErrors = document.querySelectorAll(".error")
    allErrors.forEach(span => span.remove());

    displayStripeErrors("");

    try {
        // First make sure that if use shipping is checked, we are getting that data!
        copyShippingInput();
        
        // 1. Validate Stripe card first
        // DEBUG
        console.log('Creating Stripe token...');
        const {token, error} = await stripe.createToken(card);

        if (error) {
            // DEBUG
            console.error('Stripe token error:', error);
            displayStripeErrors(error.message);
            this.disabled = false;
            return;
        }

        // DEBUG
        console.log('Stripe token created successfully:', token);

        // 2. Gather form data
        const allForms = document.querySelectorAll('.order-forms');
        // DEBUG
        console.log('Found forms:', allForms.length);
        let allFormsData = {};
        allForms.forEach(form => {
            let formId = form.id;
            // DEBUG
            console.log('Processing form:', formId);
            eachFormData = new FormData(form);
            let objectData = {};
            eachFormData.forEach((value, key) => {
                objectData[key] = value;
            });
            allFormsData[formId] = objectData
            // DEBUG
            console.log('Form data for', formId, ':', objectData);
        });

        // 3. Add Stripe token to the data
        allFormsData['stripe_token'] = token.id;

        // DEBUG
        console.log('Final data being sent:', allFormsData);

        // 4. send ajax request
        jQuery.ajax({
            url: 'checkout',
            type: 'POST',
            data: JSON.stringify(allFormsData),
            contentType: 'application/json',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            success: function (response) {
                // DEBUG
                console.log('Raw response:', response);

                // DEBUG
                try {
                    response = JSON.parse(response)
                    // DEBUG
                    console.log('Parsed response:', response);
                } 
                catch (parseError) {
                    // DEBUG
                    console.error('Error parsing response:', parseError);
                    displayStripeErrors('Invalid response from server');
                    return;
                }
                

                if (response.status === 'success') {
                    window.location.href = response.redirect_url
                }

                else if (response.status === 'error') {
                    // DEBUG
                    console.log('Error response details:', response);

                    // Check for stripe specific errors
                    if (response.stripe_error) {
                        displayStripeErrors(response.stripe_error);
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
                console.error("AJAX Error:", textStatus, errorThrown);
                console.error("Response Text:", jqXHR.responseText);
                console.error("Status:", jqXHR.status)
                alert("An error occurred during submission.");
                // Consider displaying a general error message on the page if the AJAX call itself fails
            }
        });
    } catch (error) {
        console.error('Caught error:', error);
        displayStripeErrors('An error occurred processing your payment. Please try again.');
    } finally {
        this.disabled = false;
    }
    return false;
}


// EVENT LISTENERS
placeOrderBtn.addEventListener('click', submitData);
useShipping.addEventListener('change', copyShippingInput);
document.addEventListener("DOMContentLoaded", () => copyShippingInput());


