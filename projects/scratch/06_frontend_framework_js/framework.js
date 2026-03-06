function h(tag, props, ...children) {
  return { tag, props: props || {}, children: children.flat() };
}

function createNode(vnode) {
  if (typeof vnode === "string" || typeof vnode === "number") {
    return document.createTextNode(String(vnode));
  }
  const node = document.createElement(vnode.tag);
  for (const [k, v] of Object.entries(vnode.props || {})) {
    if (k.startsWith("on") && typeof v === "function") {
      node.addEventListener(k.slice(2).toLowerCase(), v);
    } else {
      node.setAttribute(k, v);
    }
  }
  for (const child of vnode.children || []) {
    node.appendChild(createNode(child));
  }
  return node;
}

function changed(a, b) {
  return typeof a !== typeof b ||
    ((typeof a === "string" || typeof a === "number") && a !== b) ||
    (a && b && a.tag !== b.tag);
}

function patch(parent, oldVNode, newVNode, index = 0) {
  const existing = parent.childNodes[index];
  if (!oldVNode) {
    parent.appendChild(createNode(newVNode));
    return;
  }
  if (!newVNode) {
    if (existing) parent.removeChild(existing);
    return;
  }
  if (changed(oldVNode, newVNode)) {
    parent.replaceChild(createNode(newVNode), existing);
    return;
  }
  if (typeof newVNode === "string" || typeof newVNode === "number") return;

  const max = Math.max(oldVNode.children.length, newVNode.children.length);
  for (let i = 0; i < max; i++) {
    patch(existing, oldVNode.children[i], newVNode.children[i], i);
  }
}

function createSignal(initial) {
  let value = initial;
  const listeners = new Set();
  return {
    get: () => value,
    set: (v) => {
      value = v;
      for (const l of listeners) l(value);
    },
    subscribe: (l) => listeners.add(l)
  };
}

function mount(root, view, signal) {
  let oldTree = view();
  root.appendChild(createNode(oldTree));
  signal.subscribe(() => {
    const newTree = view();
    patch(root, oldTree, newTree, 0);
    oldTree = newTree;
  });
}

window.Mini = { h, createSignal, mount };
