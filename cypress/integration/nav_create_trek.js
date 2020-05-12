describe('Create trek', () => {
  beforeEach(() => {
      const username = 'admin'
      const password = 'admin'
      cy.request('/login/?next=/')
        .its('body')
        .then((body) => {
          // we can use Cypress.$ to parse the string body
          // thus enabling us to query into it easily
          const $html = Cypress.$(body)
          const csrf = $html.find('input[name=csrfmiddlewaretoken]').val()

          cy.loginByCSRF(csrf, username, password)
          .then((resp) => {
            expect(resp.status).to.eq(200)
          })
        })
  })

  it('Create path', () => {
    cy.visit('http://localhost:8000/path/list')
    cy.get("a.btn-success[href='/path/add/']").contains('Add a new path').click()
    cy.get("a.leaflet-draw-draw-polyline").click()
    cy.get('.leaflet-map-pane')
      .click(390, 250)
      .click(400, 50)
      .click(450, 50)
      .click(450, 150)
      .click(450, 150);
    cy.get("input[name='name']").type('Path number 1')
    cy.get('#save_changes').click()
    cy.url().should('not.include', '/path/add/')
    cy.get('.content').should('contain', 'Path number 1')
  })

  it('Create path split', () => {
    cy.visit('http://localhost:8000/path/list')
    cy.get("a.btn-success[href='/path/add/']").contains('Add a new path').click()
    cy.get("a.leaflet-draw-draw-polyline").click()
    cy.get('.leaflet-map-pane')
      .click(380, 220)
      .click(405, 290)
      .click(405, 290);
    cy.get("input[name='name']").type('Path number 2')
    cy.get('#save_changes').click()
    cy.url().should('not.include', '/path/add/')
    cy.get('.content').should('contain', 'Path number 2')
  })
  it('Path list', () => {
    cy.visit('http://localhost:8000/path/list')
    cy.get("a[title='Path number 1']").should('have.length', 2)
    cy.get("a[title='Path number 2']").should('have.length', 2)
  })
  it('Path action delete multiple without path', () => {
    cy.visit('http://localhost:8000/path/list')
    cy.get("a.btn-primary[data-toggle='dropdown']").click()
    cy.get("a[href='#delete']").click()
    cy.url().should('include', '/path/list/')
    cy.get("a[title='Path number 1']").should('have.length', 2)
    cy.get("a[title='Path number 2']").should('have.length', 2)
  })
  it('Path action delete multiple path', () => {
    cy.visit('http://localhost:8000/path/list')
    cy.get("input[name='path[]'][value='1']").click()
    cy.get("input[name='path[]'][value='2']").click()
    cy.get("a.btn-primary[data-toggle='dropdown']").click()
    cy.get("a[href='#delete']").click()
    cy.get("input[value='Yes, delete']").click()
    cy.url().should('include', '/path/list/')
    cy.get("a[title='Path number 1']").should('have.length', 1)
    cy.get("a[title='Path number 2']").should('have.length', 1)
  })
  it('Path action delete multiple path', () => {
    cy.visit('http://localhost:8000/path/list')
    cy.get("input[name='path[]'][value='3']").click()
    cy.get("input[name='path[]'][value='4']").click()
    cy.get("a.btn-primary[data-toggle='dropdown']").click()
    cy.get("a[href='#confirm-merge']").click()
    cy.get("button").contains('Merge').click()
    cy.url().should('include', '/path/list/')
    cy.get("a[title='Path number 1']").should('have.length', 1)
    cy.get("a[title='Path number 2']").should('have.length', 0)
  })
})
