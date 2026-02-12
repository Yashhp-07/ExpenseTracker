document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. Get All Elements ---
    const form = document.getElementById('group-expense-form');
    const amountInput = document.getElementById('amount');
    
    // "Paid By" elements
    const paidByBtn = document.getElementById('paid-by-btn');
    const memberList = document.getElementById('member-list');
    const paidByRadios = document.querySelectorAll('input[name="paid_by"]');

    // View Toggling elements
    const simpleSplitView = document.getElementById('simple-split-view');
    const advancedSplitView = document.getElementById('advanced-split-view');
    const changeSplitBtn = document.getElementById('change-split-btn');
    const fewerOptionsBtn = document.getElementById('fewer-options-btn');

    // Advanced View Tabs
    const splitMethodTabs = document.getElementById('split-method-tabs');
    const tabLinks = splitMethodTabs.querySelectorAll('.nav-link');
    const splitMethodField = document.getElementById('split-method-field');

    // Tab Content Panes
    const splitEqualContent = document.getElementById('split-equal-content');
    const splitExactContent = document.getElementById('split-exact-content');
    const splitPercentageContent = document.getElementById('split-percentage-content');
    const splitSharesContent = document.getElementById('split-shares-content');

    // "Split Equally" elements
    const equalCheckboxes = document.querySelectorAll('.split-member-check');
    const selectAllBtn = document.getElementById('select-all-btn');
    const selectNoneBtn = document.getElementById('select-none-btn');
    const equalSplitSummary = document.getElementById('equal-split-summary');

    // "Split Exact" elements
    const exactInputs = document.querySelectorAll('.exact-amount-input');
    const exactSplitSummary = document.getElementById('exact-split-summary');

    // "Split Percentage" elements
    const percentageInputs = document.querySelectorAll('.percentage-input');
    const percentageSplitSummary = document.getElementById('percentage-split-summary');

    // "Split Shares" elements
    const shareInputs = document.querySelectorAll('.share-input');
    const sharesSplitSummary = document.getElementById('shares-split-summary');
    
    // Hidden share fields
    const hiddenShareFields = document.querySelectorAll('.member-share-field');

    // --- 2. Initial State Setup ---
    function setInitialPaidByButton() {
        let checkedRadio = document.querySelector('input[name="paid_by"]:checked');
        
        // ** NEW CODE STARTS HERE **
        // If no radio is checked by default (from the template failing),
        // let's check the very first one in the list.
        if (!checkedRadio) {
            const firstRadio = document.querySelector('input[name="paid_by"]');
            if (firstRadio) {
                firstRadio.checked = true;
                checkedRadio = firstRadio; // Update our variable to this newly checked radio
            }
        }
        // ** NEW CODE ENDS HERE **
        
        // Original logic (now runs with a guaranteed 'checkedRadio')
        if (checkedRadio) {
            paidByBtn.textContent = checkedRadio.dataset.name;
        }
        updateActiveSplit(); // Calculate initial split
    }
    setInitialPaidByButton();


    // --- 3. View Toggling Logic (Simple <-> Advanced) ---
    changeSplitBtn.addEventListener('click', function() {
        simpleSplitView.style.display = 'none';
        advancedSplitView.style.display = 'block';
        updateActiveSplit();
    });

    fewerOptionsBtn.addEventListener('click', function() {
        advancedSplitView.style.display = 'none';
        simpleSplitView.style.display = 'block';
        
        // Reset to default "Split Equally"
        splitMethodTabs.querySelector('.nav-link[data-method="equal"]').click();
        selectAllBtn.click();
        changeSplitBtn.textContent = 'Equally';
        updateActiveSplit();
    });

    // --- 4. "Paid By" Button Logic ---
    paidByBtn.addEventListener('click', function() {
        memberList.style.display = memberList.style.display === 'none' ? 'block' : 'none';
    });

    paidByRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.checked) {
                paidByBtn.textContent = this.dataset.name;
                memberList.style.display = 'none';
            }
        });
    });

    // --- 5. Advanced Tab Switching Logic ---
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            tabLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            const method = this.dataset.method;
            splitMethodField.value = method;
            changeSplitBtn.textContent = this.textContent;

            // Show/hide all content panes
            splitEqualContent.style.display = (method === 'equal') ? 'block' : 'none';
            splitExactContent.style.display = (method === 'exact') ? 'block' : 'none';
            splitPercentageContent.style.display = (method === 'percentage') ? 'block' : 'none';
            splitSharesContent.style.display = (method === 'shares') ? 'block' : 'none';
            
            updateActiveSplit(); // Re-calculate on tab switch
        });
    });

    // --- 6. Core Calculation Functions ---
    
    /** Gets the total amount from the input field */
    function getTotalAmount() {
        return parseFloat(amountInput.value) || 0;
    }

    /** Updates all hidden share fields based on a Map of {memberId: share} */
    function updateHiddenShareFields(sharesMap) {
        hiddenShareFields.forEach(field => {
            const memberId = field.id.slice('share_field_'.length); 
            const share = sharesMap.get(memberId) || 0;
            field.value = share.toFixed(2);
        });
    }

    /** Calculates and updates UI for "Split Equally" */
    function calculateEqualSplit() {
        const totalAmount = getTotalAmount();
        const checkedBoxes = document.querySelectorAll('.split-member-check:checked');
        const memberCount = checkedBoxes.length;
        const share = (memberCount > 0) ? (totalAmount / memberCount) : 0;

        equalSplitSummary.textContent = `Rs ${share.toFixed(2)} / person`;

        const sharesMap = new Map();
        equalCheckboxes.forEach(box => {
            sharesMap.set(box.value, box.checked ? share : 0);
        });
        
        updateHiddenShareFields(sharesMap);
    }

    /** Calculates and updates UI for "Split by Exact Amounts" */
    function calculateExactSplit() {
        const totalAmount = getTotalAmount();
        let currentSum = 0;
        const sharesMap = new Map();

        exactInputs.forEach(input => {
            const amount = parseFloat(input.value) || 0;
            currentSum += amount;
            sharesMap.set(input.dataset.memberId, amount);
        });

        const remaining = totalAmount - currentSum;
        
        exactSplitSummary.textContent = `Remaining: Rs ${remaining.toFixed(2)}`;
        if (remaining.toFixed(2) == '0.00') {
            exactSplitSummary.className = 'mt-3 alert alert-success';
        } else {
            exactSplitSummary.className = 'mt-3 alert alert-danger';
        }

        updateHiddenShareFields(sharesMap);
    }
    
    /** NEW: Calculates and updates UI for "Split by Percentage" */
    function calculatePercentageSplit() {
        const totalAmount = getTotalAmount();
        let totalPercentage = 0;
        const sharesMap = new Map();

        percentageInputs.forEach(input => {
            const percent = parseFloat(input.value) || 0;
            totalPercentage += percent;
            const share = totalAmount * (percent / 100);
            sharesMap.set(input.dataset.memberId, share);
        });

        // Update summary
        percentageSplitSummary.textContent = `Total: ${totalPercentage.toFixed(0)}%`;
        if (totalPercentage.toFixed(0) == 100) {
            percentageSplitSummary.className = 'mt-3 alert alert-success';
        } else {
            percentageSplitSummary.className = 'mt-3 alert alert-danger';
        }
        updateHiddenShareFields(sharesMap);
    }

    /** NEW: Calculates and updates UI for "Split by Shares" */
    function calculateShareSplit() {
        const totalAmount = getTotalAmount();
        let totalShares = 0;
        const memberShares = []; // Need to store them first

        shareInputs.forEach(input => {
            // Default to 1 share if empty, for convenience
            const shares = parseFloat(input.value || (input.placeholder || 0)) || 0;
            totalShares += shares;
            memberShares.push({ id: input.dataset.memberId, shares: shares });
        });
        
        const sharesMap = new Map();
        for (const member of memberShares) {
            const share = (totalShares > 0) ? (totalAmount * (member.shares / totalShares)) : 0;
            sharesMap.set(member.id, share);
        }
        
        // Update summary
        const perShareValue = (totalShares > 0) ? (totalAmount / totalShares) : 0;
        sharesSplitSummary.textContent = `Total: ${totalShares} shares (Rs ${perShareValue.toFixed(2)} / share)`;
        sharesSplitSummary.className = 'mt-3 alert alert-info';

        updateHiddenShareFields(sharesMap);
    }
    
    /** Main dispatcher function to call the correct calculation */
    function updateActiveSplit() {
        const method = splitMethodField.value;
        if (method === 'equal') {
            calculateEqualSplit();
        } else if (method === 'exact') {
            calculateExactSplit();
        } else if (method === 'percentage') {
            calculatePercentageSplit();
        } else if (method === 'shares') {
            calculateShareSplit();
        }
    }

    // --- 7. Event Listeners for Calculations ---
    
    // Re-calculate when total amount changes
    amountInput.addEventListener('input', updateActiveSplit);

    // "Equal" listeners
    equalCheckboxes.forEach(box => box.addEventListener('change', calculateEqualSplit));
    selectAllBtn.addEventListener('click', () => {
        equalCheckboxes.forEach(box => box.checked = true);
        calculateEqualSplit();
    });
    selectNoneBtn.addEventListener('click', () => {
        equalCheckboxes.forEach(box => box.checked = false);
        calculateEqualSplit();
    });

    // "Exact" listeners
    exactInputs.forEach(input => input.addEventListener('input', calculateExactSplit));
    
    // "Percentage" listeners
    percentageInputs.forEach(input => input.addEventListener('input', calculatePercentageSplit));

    // "Shares" listeners
    shareInputs.forEach(input => input.addEventListener('input', calculateShareSplit));


    // --- 8. AJAX Form Submission ---
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Ensure calculations are final before submitting
        updateActiveSplit(); 
        
        const formData = new FormData(form);
        const url = form.action;

        // Validation Check: Ensure exact/percentage splits add up
        const method = splitMethodField.value;
        if (method === 'exact') {
            if (exactSplitSummary.classList.contains('alert-danger')) {
                alert('The exact amounts do not add up to the total. Please correct them.');
                return; // Stop submission
            }
        } else if (method === 'percentage') {
             if (percentageSplitSummary.classList.contains('alert-danger')) {
                alert('The percentages do not add up to 100%. Please correct them.');
                return; // Stop submission
            }
        }

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                alert(data.message || 'An error occurred. Please check your inputs.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An unexpected error occurred while saving.');
        });
    });

});
