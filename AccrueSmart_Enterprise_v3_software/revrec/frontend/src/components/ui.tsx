
export function Button(props:any){ return <button {...props} className={"px-3 py-2 rounded border "+(props.className||"")}>{props.children}</button>; }
export function Card(props:any){ return <div {...props} className={"bg-white rounded-xl border p-4 "+(props.className||"")}>{props.children}</div>; }
export function Input(props:any){ return <input {...props} className={"border rounded px-2 py-1 "+(props.className||"")} />; }
export function Textarea(props:any){ return <textarea {...props} className={"border rounded p-2 "+(props.className||"")} />; }
