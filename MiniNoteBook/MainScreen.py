import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import requests
import threading

class SimpleUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PDF Reader")
        self.root.geometry("800x600")

        # Prompt textbox
        tk.Label(self.root, text="Enter your question about the attached PDF:").pack(padx=10, pady=(10, 0), anchor="w")
        self.textbox = tk.Entry(self.root, width=60)
        self.textbox.pack(padx=10, pady=5)

        # PDF attachment
        self.pdf_path = None
        self.file_label = tk.Label(self.root, text="No file attached")
        self.file_label.pack(padx=10, pady=(0,5), anchor="w")
        self.attach_button = tk.Button(self.root, text="Attach PDF", command=self.attach_pdf)
        self.attach_button.pack(padx=10, pady=(0,10))

        # Submit button
        self.send_button = tk.Button(self.root, text="Submit", command=self.send)
        self.send_button.pack(padx=10, pady=5)

        # Response display
        tk.Label(self.root, text="Response:").pack(padx=10, pady=(10, 0), anchor="w")
        self.response_text = scrolledtext.ScrolledText(self.root, width=70, height=15, wrap=tk.WORD)
        self.response_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def send(self):
        user_input = self.textbox.get()
        if not user_input.strip():
            messagebox.showwarning("Empty Input", "Please enter a query")
            return
        if not self.pdf_path:
            messagebox.showwarning("No PDF", "Please attach a PDF file first")
            return
        
        # Run send_request in a separate thread to avoid blocking UI
        threading.Thread(target=self.send_request, args=(user_input,), daemon=True).start()

    def send_request(self, query):
        try:
            self.response_text.insert(tk.END, f"\n[Sending query...]\n")
            self.response_text.see(tk.END)

            # Upload the PDF as multipart/form-data; server expects an UploadFile named 'file'
            with open(self.pdf_path, "rb") as f:
                files = {"file": (self.pdf_path.split("\\")[-1], f, "application/pdf")}
                data = {"query": query}
                print(f"Sending query: {query}"," PDF: {self.pdf_path}")
                response = requests.post(
                    "http://127.0.0.1:9001/chat",
                    data=data,
                    files=files,
                    timeout=3000
                )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("answer", "No answer received")
                self.response_text.insert(tk.END, f"Query: {query}\n")
                self.response_text.insert(tk.END, f"Response: {answer}\n")
                self.response_text.insert(tk.END, "-" * 50 + "\n")
                self.textbox.delete(0, tk.END)
                print(f"Response: {answer}")
            else:
                error_msg = f"Error: {response.status_code} - {response.text}"
                self.response_text.insert(tk.END, f"{error_msg}\n")
                print(error_msg)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.response_text.insert(tk.END, f"{error_msg}\n")
            print(error_msg)
        finally:
            self.response_text.see(tk.END)

    def attach_pdf(self):
        file = filedialog.askopenfilename(filetypes=[("PDF Files","*.pdf")])
        if file:
            self.pdf_path = file
            self.file_label.config(text=file)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    ui = SimpleUI()
    ui.run()
