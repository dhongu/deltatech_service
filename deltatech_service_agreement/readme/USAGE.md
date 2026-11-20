## Configuration

1. Tick **Service Invoice** on the sales journal used for services (Invoicing → Configuration → Journals). The
   **Service → Agreement → Service Invoice** menu only lists invoices of journals with this box ticked.

   ![Sales journal form with the Service Invoice box ticked under Sequence Prefix; the box is highlighted](../static/description/en/05_jurnal_facturi_servicii.png)

2. Create an agreement type in **Service → Configuration → Services Agreement Type** and pick the sales journal
   (required). Optionally create **Service Group** records to group agreements in reports.

   ![List of service agreement types with a single row, Abonamente servicii IT](../static/description/en/04_tip_contract.png)

3. Check the billing cycles and the service periods (**Service → Configuration → Cycle** and **Date Ranges**):
   preparing the billing needs a period for the month you invoice.

## Usage

### 1. Create an agreement

Open **Service → Agreement → Services Agreements** and click **New**.

![Agreements list with the columns Reference, Agreement Date, Partner, Description, Status, Type, Salesperson, Total consumption, Total invoiced and Company; two agreements are In Progress and one is Draft](../static/description/en/01_lista_contracte.png)

Fill in the **Partner**, the **Billing Cycle** and the **Invoice Day** (the day of the month; **-1** means the last
day of the month, **0** means no fixed day), the **Payment Terms**, and add the service lines with quantity, unit
price, **Quantity Free** (not invoiced) and, optionally, **Has free cycles** / **Free cycles**. Click **Set In
Progress** to activate the agreement.

![New agreement in Draft: partner Atelier Mecanic SRL, monthly billing cycle, invoice day -1, payment terms 30 days and one service line; the partner, billing cycle, invoice day and the Set In Progress button are highlighted](../static/description/en/02_contract_nou.png)

Only agreements **In Progress** are billed. The **Next Invoice Date** is computed from the last posted invoice (or
the agreement date), the cycle and the invoice day.

![Agreement AG/00001 In Progress with two service lines and the Next Invoice Date; the Close Contract button and the Next Invoice Date field are highlighted](../static/description/en/03_contract_in_derulare.png)

### 2. Prepare the billing

In the agreements list, select the agreements and click **Billing Preparation** (managers only). Pick the
**Period** (required) and click **Apply**: one consumption in the state *Without invoice* is created for each
agreement line.

![Billing Preparation window with the Period field open and the period 2026/11 listed, above the list of agreements in progress; the Period field and the Apply button are highlighted](../static/description/en/06_pregatire_facturare.png)

### 3. Check and correct the consumptions

Open **Service → Agreement → Services Consumption**. While a consumption is *Without invoice* you can correct its
quantity, price or partner on its form.

![Services Consumption list with three consumptions for period 2026/11, quantities 10, 1 and 1 and prices 150 and 1,200; the quantity and price of the first row are highlighted](../static/description/en/07_consumuri_pregatite.png)

Select consumptions and use the **Action** menu for bulk changes:

- **Price Change**: sets a new unit price, currency and reference on the selected unbilled consumptions of a
  product. It also updates the list price of the product.

  ![Price Change window with product Suport tehnic (ore), unit price 150, currency RON and an empty Reference field; the unit price and the reference are highlighted](../static/description/en/08_modificare_pret.png)

- **Distribution**: spreads a quantity or an amount over the selected consumptions (**Fix** gives each one the
  entered value, **Divide** splits it equally).

  ![Distribution window with distribution type Quantity, mode Fix, product Suport tehnic (ore) and quantity 10; the type, mode and quantity are highlighted](../static/description/en/09_distributie.png)

- **Change Invoice Date**: sets the invoice date of the selected unbilled consumptions.

  ![Change Invoice Date window with the date Nov 30 filled in; the Invoice Date field is highlighted](../static/description/en/10_schimbare_data.png)

### 4. Invoice

Open **Service → Agreement → Billing** (or select consumptions and use **Action → Billing**). Choose the
**Journal**, how invoices are grouped (**Group by agreement**, **Group by partner** or **Split by agreement
line**) and optionally **Group by service**, then click **Apply**. Draft customer invoices are created and the
consumptions become *With invoice*. Consumptions that do not exceed the free quantity become *Not Applicable*.
A consumption with a negative quantity is invoiced as a correction that refers to the original invoice; if the
net amount of the document is negative, a credit note is created.

![Billing window with journal Sales, group by agreement, Group by service unticked and the list of the three consumptions; the journal and grouping fields are highlighted](../static/description/en/11_facturare.png)

### 5. Check and post the invoices

The generated invoices open automatically; later use **Service → Agreement → Service Invoice**.

![List of service invoices: one posted invoice for Ferma Verde SRL and one draft for Transport Rapid SRL, both dated Nov 30](../static/description/en/12_facturi_generate.png)

Open an invoice, check its lines and the note referring to the agreement, then confirm it. The **Consumption**
smart button opens its consumptions.

![Posted customer invoice INV/2026/00001 for Ferma Verde SRL with two service lines at 21% VAT and the Consumption button highlighted](../static/description/en/13_factura_servicii.png)

![Journal Items tab of the posted invoice: 411100 Customers debit 3,267 lei, 704000 credit 1,500 and 1,200 lei and 442700 VAT collected credit 567 lei](../static/description/en/15_nota_contabila.png)

On posting, the agreement stores the **Last Invoice** and recomputes the **Next Invoice Date** and its totals.

![Agreement AG/00001 after billing: Last Invoice INV/2026/00001, Next Invoice Date next month and the Invoiced button showing 2,700 lei; these fields and the button are highlighted](../static/description/en/14_contract_dupa_facturare.png)

## Automatic billing

A daily scheduled action (**Billing automation**) prepares and invoices, as draft invoices, the agreements *In
Progress* with billing automation set to *Auto* that are due and have no consumption yet in the current month.
It needs exactly one service period for the current month and a sales journal for each company. The *Billing
automation* setting is not shown on the agreement form; by default agreements are *Manual*.

## Limitations

- Users without a service role can only read agreements and consumptions; service users cannot create
  agreements (managers can).
- An agreement can be deleted only in Draft, and an invoiced consumption cannot be deleted.
- Cancelling or deleting an invoice puts its consumptions back *Without invoice*.
