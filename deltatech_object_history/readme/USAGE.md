## Configuration

Give the **Object history admin** group to the users who keep the history (Settings → Users & Companies →
Users). The administrator gets it on install. Only this group sees the **History** button and the
**Contacts → History** menu.

## Usage

### 1. Open the history of a partner

Open a partner in **Contacts**. The **History** button shows how many history rows the partner has.

![Partner form of Ferma Verde SRL; the History button with the count 2 is highlighted next to Sales, Invoiced and Due](../static/description/en/01_partener_buton_istoric.png)

Click **History** to list the rows of the partner, newest first. **New** in this list creates a row already
linked to the partner, with **Related partner** and **Parent name** filled in.

![History list opened from the partner: two rows by Andrei Popescu with the columns Created on, Created by, Parent name, Related partner, Name and Description](../static/description/en/03_istoric_partener.png)

### 2. Add a row from the Action menu

On the partner form, click **⚙ Actions → Add history**, fill in **Name** (required) and **Description**, then
click **Add**. A row added this way has no **Related partner** and no **Parent name**; to get them, use
**New** from the **History** button instead. This action exists only on partners.

![Add history dialog over the partner form: the Name and Description fields and the Add button are highlighted; Resource Model res.partner and Resource ID Ferma Verde SRL on the right](../static/description/en/02_adaugare_istoric.png)

### 3. Read a history row

A row shows its **Name**, **Related partner** (required when saving), the linked document (**Resource
Model**, **Resource ID**, **Parent name**) and the **Description**. **Open Document** and **Open** go back
to the original record. Each row has its own chatter.

![History row form: Related partner and Parent name Ferma Verde SRL and the Open button are highlighted; the description is below](../static/description/en/04_rand_istoric.png)

### 4. History on invoices and transfers

The same **History** button appears on invoices / journal entries and on stock transfers. **New** from its
list fills in **Parent name** with the document number; choose the **Related partner** before saving.

![Posted customer invoice INV/2026/00001 for Ferma Verde SRL; the History button with the count 1 is highlighted](../static/description/en/05_factura_istoric.png)

### 5. Search all rows

**Contacts → History → History lines** lists every row you can access. Use the filters **Partners**,
**Moves** and **Transfers**, or group by **Partner** or by **Parent** (the document type).

![History lines list with three rows by Andrei Popescu: one on the invoice INV/2026/00001 and two on the partner Ferma Verde SRL](../static/description/en/06_lista_istoric.png)

Rows are visible only to users who can read their document. No user can delete a row; **Object history admin** can archive rows from the list (**Actions → Archive**).
