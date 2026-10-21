const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

test('photo URLs use their actual product origin and never invent another brand image', () => {
  const context = vm.createContext({ URL, document: { addEventListener() {} } });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../js/core.js'), 'utf8'), context);
  assert.equal(context.formatImgUrl('/photos/a.jpg?v=2', 'Unknown vendor', 'Laptop', 'https://shop.example/product'), 'https://shop.example/photos/a.jpg?v=2');
  assert.equal(context.formatImgUrl('//cdn.example/photo.jpg', '', ''), 'https://cdn.example/photo.jpg');
  assert.equal(context.formatImgUrl('', 'Lenovo', 'Lenovo laptop'), '');
  assert.equal(context.formatImgUrl('/unknown.jpg', '', ''), '');
  assert.equal(context.formatImgUrl('javascript:alert(1)', '', ''), '');
  assert.equal(context.formatImgUrl('https://user:password@cdn.example/photo.jpg', '', ''), '');
});
